extends Node2D
# All entity/status data comes from public Python snapshots/facts.
# Only message positions use render time; pending markers stop before arrival.
const Client = preload("res://scripts/event_client.gd")
const TEAMS = ["product", "architecture", "security", "engineering", "operations"]
const ORIGINS = [Vector2(24, 172), Vector2(334, 172), Vector2(644, 172), Vector2(174, 420), Vector2(484, 420)]
const INK = Color("e1eafa")
const MUTED = Color("97abc8")
const HUMAN = Color("73c6ea")
const AGENT = Color("d2b2ff")
const MESSAGE = Color("ffd17a")

var autostart: bool = true
var snapshot: Dictionary = {}
var transfers: Dictionary = {}
var positions: Dictionary = {}
var progress: Dictionary = {}
var feed_event_ids: Array[String] = []
var feed_lines: Array[String] = []
var connection: String = "No source configured"
var font: Font = ThemeDB.fallback_font
var feed: RichTextLabel
var details: RichTextLabel
var artifacts: RichTextLabel
var elapsed: float = 0.0
var fixture: Dictionary = {}
var fixture_stage: int = 0
var fixture_wait: float = 0.0
var capture_path: String = ""
var capture_after: float = 7.0
var captured: bool = false

func panel(rect: Rect2, size: int = 17, follow: bool = false) -> RichTextLabel:
	var box = RichTextLabel.new()
	box.position = rect.position
	box.size = rect.size
	box.add_theme_font_size_override("normal_font_size", size)
	box.add_theme_color_override("default_color", INK)
	box.bbcode_enabled = false
	box.scroll_following = follow
	add_child(box)
	return box

func _ready() -> void:
	feed = panel(Rect2(40, 770, 1360, 204), 17, true)
	details = panel(Rect2(970, 173, 442, 305), 16)
	artifacts = panel(Rect2(970, 521, 442, 197), 17)
	if not autostart:
		return
	var options: Dictionary = {}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--") and "=" in argument:
			var pair = argument.substr(2).split("=", true, 1)
			options[pair[0]] = pair[1]
	capture_path = options.get("capture", "")
	capture_after = float(options.get("capture-after", "7"))
	if options.has("fixture"):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(options.fixture))
		if not parsed is Dictionary or not parsed.get("stages") is Array:
			set_connection("Invalid fixture; playback stopped")
			return
		fixture = parsed
		var validator = Client.new()
		if not validator.install_snapshot(fixture.initial_snapshot):
			set_connection("Invalid fixture snapshot")
			validator.free()
			return
		install_snapshot(fixture.initial_snapshot)
		validator.free()
		set_connection("Recorded Python fixture · passive playback")
	else:
		var client = Client.new()
		add_child(client)
		client.snapshot_received.connect(install_snapshot)
		client.events_received.connect(apply_events)
		client.connection_changed.connect(set_connection)
		client.start(options.get("endpoint", ""), options.get("run-id", ""))

func set_connection(message: String) -> void:
	connection = message
	queue_redraw()

func install_snapshot(value: Dictionary) -> void:
	if snapshot.get("run_id", "") != value.run_id:
		feed_event_ids.clear()
		feed_lines.clear()
		progress.clear()
	var changed = snapshot.get("snapshot_id", "") != value.snapshot_id
	snapshot = value.duplicate(true)
	transfers.clear()
	for transfer in snapshot.transfers:
		transfers[transfer.transfer_id] = transfer.duplicate(true)
		if not progress.has(transfer.transfer_id):
			progress[transfer.transfer_id] = 0.0 if transfer.status == "pending" else 1.0
	positions.clear()
	for team_index in TEAMS.size():
		var row = 0
		for actor in snapshot.roster:
			if actor.team_id == TEAMS[team_index]:
				positions[actor.actor_id] = ORIGINS[team_index] + Vector2(24, 64 + row * 42)
				row += 1
	_refresh_text()
	if changed and autostart:
		var proposal_ids: Array = []
		for proposal in snapshot.proposals:
			proposal_ids.append(proposal.proposal_id)
		var statuses: Dictionary = {}
		for transfer in transfers.values():
			statuses[transfer.transfer_id] = transfer.status
		print(JSON.stringify({"projection_snapshot": snapshot.snapshot_id, "actor_ids": actor_ids(),
			"proposal_ids": proposal_ids, "transfer_statuses": statuses}))
	queue_redraw()

func apply_events(events: Array) -> void:
	for event in events:
		if event.event_id in feed_event_ids:
			continue
		feed_event_ids.append(event.event_id)
		var payload: Dictionary = event.payload
		if event.event_type == "TransferSent":
			# A refresh can already contain this send's terminal fact.
			if not transfers.has(payload.transfer_id):
				transfers[payload.transfer_id] = payload.duplicate(true)
				transfers[payload.transfer_id]["status"] = "pending"
				transfers[payload.transfer_id]["sent_tick"] = event.tick
				progress[payload.transfer_id] = 0.0
		elif event.event_type in ["KnowledgeTransferred", "InformationLost"] and transfers.has(payload.transfer_id):
			transfers[payload.transfer_id]["status"] = "received" if event.event_type == "KnowledgeTransferred" else "lost"
			transfers[payload.transfer_id]["resolved_tick"] = event.tick
		var public_refs: Array[String] = []
		for key in ["actor_id", "decision_id", "channel_id", "transfer_id"]:
			if payload.get(key) is String:
				public_refs.append(payload[key])
		feed_lines.append("%s  ·  tick %d  ·  %s  %s" % [event.event_id, event.tick, event.event_type, "  ".join(public_refs)])
		if feed_lines.size() > 120:
			feed_lines.pop_front()
	_refresh_text()

func department_ids() -> Array:
	var result: Array = []
	for actor in snapshot.get("roster", []):
		if not actor.team_id in result:
			result.append(actor.team_id)
	result.sort()
	return result

func actor_ids() -> Array:
	var result: Array = positions.keys()
	result.sort()
	return result

func channel_ids() -> Array:
	var result: Array = []
	for channel in snapshot.get("channels", []):
		result.append(channel.channel_id)
	result.sort()
	return result

func public_text() -> String:
	if snapshot.is_empty():
		return "Waiting for Python public snapshot"
	var lines: Array[String] = ["Run: " + snapshot.run_id, "State: " + snapshot.snapshot_id,
		"Work Item " + snapshot.work_item.work_item_id, snapshot.work_item.text]
	for actor in snapshot.roster:
		lines.append("%s · %s · %s" % [actor.actor_id, actor.kind, actor.role])
	for channel in snapshot.channels:
		lines.append("%s: %s → %s" % [channel.channel_id, channel.sender, channel.recipient])
	for transfer in transfers.values():
		lines.append("%s · %s → %s · %s" % [transfer.transfer_id, transfer.sender, transfer.recipient, transfer.status])
	for proposal in snapshot.proposals:
		lines.append(proposal_text(proposal))
	return "\n".join(lines) + "\n" + "\n".join(feed_lines)

func proposal_text(proposal: Dictionary) -> String:
	var line = "%s\n%s · completed tick %d" % [proposal.proposal_id, proposal.actor_id, proposal.completion_tick]
	for assessment in proposal.assessments:
		line += "\n  %s: %s" % [assessment.dimension, assessment.status]
	return line

func _refresh_text() -> void:
	if feed == null:
		return
	var feed_text = "\n".join(feed_lines) if not feed_lines.is_empty() else "Waiting for new public events; earlier facts are summarized by the snapshot."
	if feed.text != feed_text:
		feed.text = feed_text
	if snapshot.is_empty():
		return
	var detail_text = "Run: %s\nState: %s\n\nDirected public channels (%d)\n" % [snapshot.run_id, snapshot.snapshot_id, snapshot.channels.size()]
	for channel in snapshot.channels:
		detail_text += "%s: %s → %s\n" % [channel.channel_id, channel.sender, channel.recipient]
	detail_text += "\nRecorded messages · contents hidden\n"
	for transfer in transfers.values():
		detail_text += "%s\n%s → %s · %s\n" % [transfer.transfer_id, transfer.sender, transfer.recipient, transfer.status]
	var artifact_text = "Work Item %s\n%s\n%d completion(s) recorded · outcome unknown\n\nChange Proposals (%d)\n" % [snapshot.work_item.work_item_id, snapshot.work_item.text, snapshot.proposals.size(), snapshot.proposals.size()]
	for proposal in snapshot.proposals:
		artifact_text += proposal_text(proposal) + "\n\n"
	_update_inspection_panel(details, detail_text)
	_update_inspection_panel(artifacts, artifact_text)

func _update_inspection_panel(box: RichTextLabel, text: String) -> void:
	if box.text == text:
		return
	var scroll_position = box.get_v_scroll_bar().value
	box.text = text
	box.get_v_scroll_bar().set_deferred("value", scroll_position)

func animate(delta: float) -> void:
	for transfer_id in transfers:
		var ceiling = 0.88 if transfers[transfer_id].status == "pending" else 1.0
		progress[transfer_id] = minf(float(progress.get(transfer_id, 0.0)) + delta / 2.0, ceiling)
	queue_redraw()

func _process(delta: float) -> void:
	elapsed += delta
	animate(delta)
	if not fixture.is_empty() and fixture_stage < fixture.stages.size():
		fixture_wait += delta
		if fixture_wait >= 1.5:
			fixture_wait = 0.0
			var stage: Dictionary = fixture.stages[fixture_stage]
			var validator = Client.new()
			validator.install_snapshot(snapshot)
			if validator.accept_batch(stage.batch) and validator.install_snapshot(stage.snapshot):
				apply_events(stage.batch.events)
				install_snapshot(stage.snapshot)
				fixture_stage += 1
			else:
				set_connection("Fixture gap; playback stopped")
				fixture = {}
			validator.free()
	if not capture_path.is_empty() and elapsed >= capture_after and not captured:
		captured = true
		capture_viewport()

func capture_viewport() -> void:
	# Explicit viewport only. A real renderer is required; headless is a separate check.
	if DisplayServer.get_name() == "headless":
		push_error("Viewport capture requires a real renderer")
		return
	await RenderingServer.frame_post_draw
	var error = get_viewport().get_texture().get_image().save_png(capture_path)
	print("Viewport PNG: %s (result %d)" % [capture_path, error])

func label_at(point: Vector2, text: String, size: int = 18, color: Color = INK, width: float = -1) -> void:
	draw_string(font, point, text, HORIZONTAL_ALIGNMENT_LEFT, width, size, color)

func _draw() -> void:
	label_at(Vector2(24, 42), "PAYMENTCO  /  ORGANIZATION", 27)
	label_at(Vector2(24, 74), "Passive preview · simulated ticks come from Python · message contents remain hidden", 18, MUTED)
	label_at(Vector2(24, 106), connection, 18, HUMAN)
	if not snapshot.is_empty():
		label_at(Vector2(1030, 106), "Tick %d  ·  cursor %d" % [snapshot.tick, snapshot.cursor], 18)
	label_at(Vector2(24, 145), "○ Human    ◇ Agent    → Directed channel    ● Recorded message", 18, MUTED)
	for index in TEAMS.size():
		draw_rect(Rect2(ORIGINS[index], Vector2(280, 220)), Color("101d30"))
		draw_rect(Rect2(ORIGINS[index], Vector2(280, 220)), Color("29415f"), false, 1)
		label_at(ORIGINS[index] + Vector2(16, 30), TEAMS[index].to_upper(), 18)
	# Directional arrows connect only actual public endpoints, behind actor labels.
	for channel in snapshot.get("channels", []):
		if not positions.has(channel.sender) or not positions.has(channel.recipient):
			continue
		var start: Vector2 = positions[channel.sender]
		var end: Vector2 = positions[channel.recipient]
		var direction = (end - start).normalized()
		var tip = end - direction * 12
		draw_line(start + direction * 12, tip, Color(0.36, 0.52, 0.70, 0.6), 1.5, true)
		draw_line(tip, tip - direction.rotated(0.5) * 10, MUTED, 1.5, true)
		draw_line(tip, tip - direction.rotated(-0.5) * 10, MUTED, 1.5, true)
	for actor in snapshot.get("roster", []):
		if not positions.has(actor.actor_id):
			continue
		var point: Vector2 = positions[actor.actor_id]
		var color = HUMAN if actor.kind == "human" else AGENT
		if actor.kind == "human":
			draw_circle(point, 7, color, false, 2, true)
		else:
			draw_colored_polygon(PackedVector2Array([point + Vector2(0, -8), point + Vector2(8, 0), point + Vector2(0, 8), point + Vector2(-8, 0)]), color)
		draw_rect(Rect2(point + Vector2(12, -18), Vector2(236, 38)), Color("101d30"))
		label_at(point + Vector2(16, -1), actor.actor_id, 18, color, 232)
		label_at(point + Vector2(16, 17), actor.role, 14, MUTED, 232)
	for transfer_id in transfers:
		var transfer: Dictionary = transfers[transfer_id]
		if not positions.has(transfer.sender) or not positions.has(transfer.recipient):
			continue
		var fraction = float(progress.get(transfer_id, 0))
		var point: Vector2 = positions[transfer.sender].lerp(positions[transfer.recipient], fraction)
		var color = MESSAGE if transfer.status == "pending" else (HUMAN if transfer.status == "received" else Color("f29a9a"))
		# A loss marker stops along its path; never claims recipient acquisition.
		if transfer.status == "lost":
			point = positions[transfer.sender].lerp(positions[transfer.recipient], minf(fraction, 0.5))
			draw_line(point - Vector2(5, 5), point + Vector2(5, 5), color, 2)
			draw_line(point + Vector2(-5, 5), point + Vector2(5, -5), color, 2)
		else:
			draw_circle(point, 5, color)
	label_at(Vector2(24, 681), "Pending markers wait for a Python receipt or loss fact; animation conveys no knowledge gain.", 16, MUTED)
	label_at(Vector2(24, 710), "Verification and validation remain separate. Scroll panels to inspect all public IDs and statuses.", 16, MUTED)
	draw_rect(Rect2(950, 135, 478, 355), Color("101d30"))
	label_at(Vector2(970, 160), "PUBLIC LINKS & MESSAGES", 19)
	draw_rect(Rect2(950, 497, 478, 225), Color("101d30"))
	label_at(Vector2(970, 519), "WORK & ASSURANCE", 19)
	draw_rect(Rect2(24, 737, 1404, 249), Color("101d30"))
	label_at(Vector2(40, 762), "PUBLIC EVENT FEED · original IDs / simulation order", 19)
