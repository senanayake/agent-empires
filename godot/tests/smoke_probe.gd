extends SceneTree

var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _initialize() -> void:
	call_deferred("probe")

func probe() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/paymentco.json"))
	var client_script = load("res://scripts/event_client.gd")
	var view_script = load("res://scripts/organization_view.gd")
	if client_script == null or view_script == null:
		push_error("Missing passive projection implementation")
		quit(1)
		return
	var client = client_script.new()
	var view = view_script.new()
	view.autostart = false
	root.add_child(client)
	root.add_child(view)
	var invalid_client = client_script.new()
	root.add_child(invalid_client)
	invalid_client.start("http://127.0.0.1:80@external.invalid/command", "test")
	check(not invalid_client.active and invalid_client.request == null, "Endpoint must use a real loopback port")
	invalid_client.free()
	check(client.install_snapshot(fixture.initial_snapshot), "Python initial snapshot admitted")
	view.install_snapshot(fixture.initial_snapshot)
	check(view.department_ids().size() == 5, "Five public departments")
	check(view.actor_ids().size() == 13, "All real humans and agents displayed")
	var initial_cursor = client.cursor
	# Refresh racing with new facts must preserve the event cursor.
	client.expected_run = fixture.initial_snapshot.run_id
	client.resync = false
	client.phase = "snapshot"
	client.pending = {"command_id": "race.snapshot"}
	var race_ack = {"version": 1, "run_id": client.expected_run, "command_id": "race.snapshot",
		"ack_id": client.expected_run + ":ack:race.snapshot", "status": "accepted",
		"result": fixture.stages[0].snapshot}
	client._completed(HTTPRequest.RESULT_SUCCESS, 200, PackedStringArray(), JSON.stringify(race_ack).to_utf8_buffer())
	check(client.cursor == initial_cursor, "Snapshot refresh cannot skip unseen event IDs")
	for mutation in ["run", "version", "gap", "order", "id", "schema", "head", "batch_id", "payload"]:
		var bad: Dictionary = fixture.stages[0].batch.duplicate(true)
		match mutation:
			"run": bad.run_id = "old-run"
			"version": bad.version = 2
			"gap": bad.events.remove_at(0)
			"order": bad.events.reverse()
			"id": bad.events[0].event_id = "fake"
			"schema": bad.events[0].schema_version = 2
			"head": bad.head_cursor = 0
			"batch_id": bad.batch_id = "fake"
			"payload": bad.events[0].payload = "invalid"
		check(not client.accept_batch(bad), "Reject malformed batch: " + mutation)
		check(client.cursor == initial_cursor, "Batch rejection is atomic")
	var bad_snapshot: Dictionary = fixture.initial_snapshot.duplicate(true)
	bad_snapshot.cursor = -1
	check(not client.install_snapshot(bad_snapshot), "Reject negative snapshot cursor")
	check(client.cursor == initial_cursor, "Snapshot rejection is atomic")
	bad_snapshot = fixture.initial_snapshot.duplicate(true)
	bad_snapshot.version = true
	check(not client.install_snapshot(bad_snapshot), "Reject boolean version")
	bad_snapshot = fixture.initial_snapshot.duplicate(true)
	bad_snapshot.roster[0].actor_id = bad_snapshot.roster[1].actor_id
	check(not client.install_snapshot(bad_snapshot), "Reject duplicate actor IDs")
	for stage in fixture.stages:
		check(client.accept_batch(stage.batch), "Admit contiguous real batch")
		view.apply_events(stage.batch.events)
		if stage == fixture.stages[0]:
			for transfer in view.transfers.values():
				check(transfer.status == "pending", "Sent never means received")
			view.animate(100.0)
			for transfer in view.transfers.values():
				check(transfer.status == "pending", "Render time never resolves transfer")
			check(view.snapshot.tick == 0, "Render time never steps Python")
		check(client.install_snapshot(stage.snapshot), "Refresh authoritative Python snapshot")
		view.install_snapshot(stage.snapshot)
		var expected: Array = []
		for actor in stage.snapshot.roster:
			expected.append(actor.actor_id)
		expected.sort()
		check(view.actor_ids() == expected, "Displayed actor IDs match Python")
		check(view.snapshot.snapshot_id == stage.snapshot.snapshot_id, "Displayed state ID equals Python")
		check(view.channel_ids().size() == stage.snapshot.channels.size(), "Displayed links match Python")
		check(view.snapshot.proposals == stage.snapshot.proposals, "Proposal IDs and assurance retained")
	check(not client.accept_batch(fixture.stages[-1].batch), "Duplicate batch rejected")
	var empty = {"version": 1, "run_id": client.run_id, "cursor": client.cursor,
		"next_cursor": client.cursor, "head_cursor": client.cursor, "events": [],
		"batch_id": "%s:batch:%d:%d" % [client.run_id, client.cursor, client.cursor]}
	check(client.accept_batch(empty), "Empty batch at head accepted")
	client.active = true
	for index in 4:
		client._recover("probe disconnect")
	check(not client.active, "Recovery stops after three retry attempts")
	check(client.cursor == fixture.stages[-1].snapshot.cursor, "Disconnect never advances domain cursor")
	var final_snapshot: Dictionary = fixture.stages[-1].snapshot
	check(view.snapshot.proposals.size() == 3, "Three recorded proposals displayed")
	for p in view.snapshot.proposals:
		var statuses: Dictionary = {}
		for assessment in p.assessments:
			statuses[assessment.dimension] = assessment.status
		check(statuses.verification_status == "pass", "Actual verification passes")
		check(statuses.validation_status == "unknown", "Unknown validation survives rendering")
	check(view.feed_event_ids.size() == final_snapshot.cursor - initial_cursor, "Every event ID retained in sequence")
	check(view.transfers.values().any(func(t): return t.status == "lost"), "Actual loss displayed")
	check(view.transfers.values().any(func(t): return t.status == "received"), "Actual receipt displayed")
	# Privacy projection: unexpected contents are never used by visible text.
	view.snapshot["private_answer"] = "SECRET_WORLD_ANSWER"
	check(not "SECRET_WORLD_ANSWER" in view.public_text(), "Private fields absent from visible text")
	var reconnect = view_script.new()
	reconnect.autostart = false
	root.add_child(reconnect)
	reconnect.install_snapshot(final_snapshot)
	check(reconnect.actor_ids() == view.actor_ids(), "Reconnect restores roster")
	check(reconnect.transfers == view.transfers, "Reconnect restores recorded terminal states")
	await process_frame
	var scene = load("res://scenes/organization.tscn").instantiate()
	scene.autostart = false
	root.add_child(scene)
	await process_frame
	reconnect.apply_events(fixture.stages[0].batch.events)
	check(reconnect.transfers == view.transfers, "Older send events cannot regress a resolved snapshot")
	# A public snapshot may race ahead of the previous event batch. Catch up
	# those event IDs before adopting it; routine polling must not drop facts.
	var polling = client_script.new()
	root.add_child(polling)
	polling.expected_run = fixture.initial_snapshot.run_id
	polling.install_snapshot(fixture.initial_snapshot)
	polling.resync = false  # model an already connected polling refresh
	polling.phase = "snapshot"
	polling.pending = {"command_id": "race.snapshot"}
	var raced_ack = {"version": 1, "run_id": polling.expected_run,
		"command_id": "race.snapshot", "ack_id": polling.expected_run + ":ack:race.snapshot",
		"status": "accepted", "result": fixture.stages[0].snapshot}
	polling._completed(HTTPRequest.RESULT_SUCCESS, 200, PackedStringArray(), JSON.stringify(raced_ack).to_utf8_buffer())
	check(polling.cursor == initial_cursor, "Routine snapshot cannot skip unconsumed events")
	check(polling.phase == "events", "Race continues by fetching missing events")
	check(polling.accept_batch(fixture.stages[0].batch), "Raced event IDs remain consumable")
	# Unchanged live polling must not snap inspection panels back to the top.
	await process_frame
	view.details.get_v_scroll_bar().value = 80.0
	var scroll_before: float = view.details.get_v_scroll_bar().value
	check(scroll_before > 0.0, "Scrollable details available for inspection")
	view.install_snapshot(final_snapshot)
	view.apply_events([])
	await process_frame
	check(is_equal_approx(view.details.get_v_scroll_bar().value, scroll_before), "Polling preserves user scroll position")
	print(JSON.stringify({"failures": failures, "snapshot_id": final_snapshot.snapshot_id,
		"actors": view.actor_ids(), "departments": view.department_ids(),
		"events_checked": view.feed_event_ids.size()}))
	quit(0 if failures.is_empty() else 1)
