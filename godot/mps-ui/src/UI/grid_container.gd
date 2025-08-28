extends GridContainer

##requests http-get from server
const GRID_PANEL_CONTAINER = preload("res://src/UI/grid_panel_container.tscn")

@onready var http_request: HTTPRequest = $HTTPRequest
@export_enum( "/farms","/pots", "/plants") var api: String = "/farms"

var table: Array = []

signal table_loaded(table)
signal detail_requested(entry)

func _ready() -> void:
	load_table()

func load_table() -> void:
	var err = http_request.request(Env.URL+Env.API+api)
	if err != OK:
		print("Request error:", err)


func display_table(_table) -> void:
	table.clear()
	table = _table
	for child in get_children():
		if child is not HTTPRequest: child.queue_free()
	for dict in table:
		if dict is String:
			load_table()
			return
	
		var rect := GRID_PANEL_CONTAINER.instantiate()
		rect.entry = dict
		rect.api = api
		rect.detail_requested.connect(_on_rect_detail_requested)
		add_child(rect)
	emit_signal("table_loaded", table)

func _on_rect_detail_requested(entry: Dictionary) -> void:
	emit_signal("detail_requested", entry)

func _on_http_request_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	print("result: %d | response_code: %d headers: %s" % [result, response_code, headers])
	if response_code != 200:
		print("Body:", body.get_string_from_utf8())
		return
	var json = JSON.new()
	var error = json.parse(body.get_string_from_utf8())
	if error != OK:
		print("JSON parse error")
		return
	display_table(json.data)
