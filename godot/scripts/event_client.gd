extends Node
# Sequential read-only transport. No step/advance/pause or domain commands.
signal snapshot_received(snapshot: Dictionary)
signal events_received(events: Array)
signal connection_changed(message: String)

var cursor: int = 0
var run_id: String = ""
var expected_run: String = ""
var endpoint: String = ""
var snapshot: Dictionary = {}
var request: HTTPRequest
var pending: Dictionary = {}
var serial: int = 0
var failures: int = 0
var phase: String = "snapshot"
var active: bool = false
var delay: float = 0.0
var client_id: String = ""
var resync: bool = true

static func integer(value: Variant, minimum: int = 0) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and float(value) == floor(float(value)) and value >= minimum

static func text_id(value: Variant) -> bool:
	return value is String and not value.strip_edges().is_empty() and value.length() <= 128

static func keyed_list(value: Variant, key: String) -> bool:
	if not value is Array:
		return false
	var seen: Dictionary = {}
	for item in value:
		if not item is Dictionary or not text_id(item.get(key)) or seen.has(item[key]):
			return false
		seen[item[key]] = true
	return true

func install_snapshot(value: Variant) -> bool:
	if not value is Dictionary or not integer(value.get("version"), 1) or value.version != 1:
		return false
	if not text_id(value.get("run_id")) or not integer(value.get("cursor")) or not integer(value.get("tick")):
		return false
	if not expected_run.is_empty() and value.run_id != expected_run:
		return false
	if not value.get("snapshot_id") is String or not value.snapshot_id.begins_with(value.run_id + ":snapshot:"):
		return false
	if not value.get("work_item") is Dictionary or not text_id(value.work_item.get("work_item_id")) or not value.work_item.get("text") is String:
		return false
	if not keyed_list(value.get("roster"), "actor_id") or not keyed_list(value.get("channels"), "channel_id") or not keyed_list(value.get("transfers"), "transfer_id") or not keyed_list(value.get("proposals"), "proposal_id"):
		return false
	for actor in value.roster:
		if actor.get("kind") not in ["human", "agent"] or not text_id(actor.get("team_id")) or not actor.get("role") is String:
			return false
	for channel in value.channels:
		if not text_id(channel.get("sender")) or not text_id(channel.get("recipient")) or not integer(channel.get("latency"), 1):
			return false
	for transfer in value.transfers:
		if not valid_transfer(transfer) or not integer(transfer.get("sent_tick")) or transfer.get("status") not in ["pending", "received", "lost"]:
			return false
	for proposal in value.proposals:
		if not text_id(proposal.get("actor_id")) or not integer(proposal.get("completion_tick")) or not proposal.get("assessments") is Array:
			return false
		for assessment in proposal.assessments:
			if not assessment is Dictionary or not text_id(assessment.get("dimension")) or not text_id(assessment.get("status")):
				return false
	snapshot = value.duplicate(true)
	run_id = value.run_id
	cursor = int(value.cursor)
	return true

static func valid_transfer(value: Dictionary) -> bool:
	return text_id(value.get("transfer_id")) and text_id(value.get("channel_id")) and text_id(value.get("sender")) and text_id(value.get("recipient")) and integer(value.get("units"), 1) and integer(value.get("delivery_tick"))

func accept_batch(batch: Variant) -> bool:
	if not batch is Dictionary or not integer(batch.get("version"), 1) or batch.version != 1 or batch.get("run_id") != run_id:
		return false
	if not integer(batch.get("cursor")) or batch.cursor != cursor or not batch.get("events") is Array or batch.events.size() > 256:
		return false
	if not integer(batch.get("next_cursor")) or batch.next_cursor != cursor + batch.events.size() or not integer(batch.get("head_cursor")) or batch.head_cursor < batch.next_cursor:
		return false
	if batch.get("batch_id") != "%s:batch:%d:%d" % [run_id, cursor, batch.next_cursor]:
		return false
	for index in batch.events.size():
		var event = batch.events[index]
		if not event is Dictionary or not integer(event.get("sequence")) or event.sequence != cursor + index or event.get("event_id") != "%s:event:%d" % [run_id, cursor + index]:
			return false
		if not integer(event.get("schema_version"), 1) or event.schema_version != 1 or not integer(event.get("tick")) or not text_id(event.get("event_type")) or not event.get("payload") is Dictionary:
			return false
		if event.event_type == "TransferSent" and not valid_transfer(event.payload):
			return false
		if event.event_type in ["KnowledgeTransferred", "InformationLost"] and not text_id(event.payload.get("transfer_id")):
			return false
	cursor = int(batch.next_cursor)
	return true

func start(url: String, wanted_run: String) -> void:
	# Loopback matches AE-020's bounded passive server, never a public endpoint.
	var port_text = url.trim_prefix("http://127.0.0.1:").trim_suffix("/command")
	if not url.begins_with("http://127.0.0.1:") or not url.ends_with("/command") or not port_text.is_valid_int() or str(port_text.to_int()) != port_text or port_text.to_int() < 1 or port_text.to_int() > 65535 or not text_id(wanted_run):
		connection_changed.emit("Invalid endpoint/run ID; restart preview")
		return
	endpoint = url
	expected_run = wanted_run
	client_id = "godot.%d" % Time.get_ticks_usec()
	request = HTTPRequest.new()
	request.timeout = 3.0
	request.body_size_limit = 1048576
	add_child(request)
	request.request_completed.connect(_completed)
	active = true
	connection_changed.emit("Connecting to Python…")

func _process(delta: float) -> void:
	if not active or not pending.is_empty():
		return
	delay -= delta
	if delay > 0:
		return
	serial += 1
	pending = {"version": 1, "run_id": expected_run, "command_id": "%s.%d" % [client_id, serial],
		"operation": phase, "args": {} if phase == "snapshot" else {"cursor": cursor, "limit": 256}}
	var error = request.request(endpoint, ["Content-Type: application/json"], HTTPClient.METHOD_POST, JSON.stringify(pending))
	if error != OK:
		_recover("Request unavailable")

func _recover(reason: String) -> void:
	pending = {}
	failures += 1
	phase = "snapshot"
	resync = true
	delay = 2.0
	active = failures <= 3
	connection_changed.emit(reason + ("; resnapshot %d/3" % failures if active else "; disconnected — restart preview"))

func _completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		_recover("Python connection lost")
		return
	var parser = JSON.new()
	if parser.parse(body.get_string_from_utf8()) != OK:
		_recover("Invalid JSON")
		return
	var ack = parser.data
	if not ack is Dictionary or ack.get("version") != 1 or ack.get("run_id") != expected_run or ack.get("command_id") != pending.command_id or ack.get("ack_id") != "%s:ack:%s" % [expected_run, pending.command_id]:
		_recover("Incompatible acknowledgment")
		return
	if code != 200 or ack.get("status") != "accepted":
		var reason = str(ack.get("error", "Rejected"))
		_recover(reason)
		if reason in ["wrong_run", "session_capacity", "incompatible_version"]:
			active = false
			connection_changed.emit(reason + "; restart preview with current run ID")
		return
	var previous_cursor = cursor
	var valid = install_snapshot(ack.get("result")) if phase == "snapshot" else accept_batch(ack.get("result"))
	if not valid:
		_recover("State gap or incompatible projection")
		return
	if phase == "snapshot":
		if not resync:
			cursor = previous_cursor  # a refresh must not skip facts arriving between polls
		resync = false
		snapshot_received.emit(snapshot)
		phase = "events"
		delay = 0.7
	else:
		events_received.emit(ack.result.events)
		phase = "snapshot"
		delay = 0.0
	pending = {}
	failures = 0
	connection_changed.emit("Connected · read-only Python state")
