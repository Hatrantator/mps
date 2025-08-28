extends Control


@export_enum( "/farms", "/plants") var api: String = "/farms"
@export_enum("request", "ready") var state: int = 1

@onready var http_request: HTTPRequest = $HTTPRequest
#main screen center container
@onready var center_container: CenterContainer = $BG/MainScreenVBoxContainer/ScrollContainer/CenterContainer
@onready var home_button: Button = $BG/MainScreenVBoxContainer/HBoxContainer/HomeButton
@onready var menu_button: Button = $BG/MainScreenVBoxContainer/HBoxContainer/MenuButton


const GRID_CONTAINER = preload("uid://n3fu4no16csc")


func _ready() -> void:
	add_main_screen(api)

func clear_main_screen() -> void:
	for child in center_container.get_children():
		child.queue_free()

func add_main_screen(_api: String) -> void:
	state = 0
	clear_main_screen()
	var grid_container = GRID_CONTAINER.instantiate()
	grid_container.api = _api
	grid_container.table_loaded.connect(_on_grid_container_table_loaded)
	grid_container.detail_requested.connect(_on_grid_container_detail_requested)
	center_container.add_child(grid_container)

func add_detail_screen(entry: Dictionary) -> void:
	state = 0
	clear_main_screen()

func delete_entry() -> void:
	print(Env.URL+Env.API+api+str(3))
	var body = str(3)
	http_request.request(
		Env.URL+Env.API+api+"/"+str(3), 
		[], 
		HTTPClient.METHOD_DELETE, 
		body
	)

func post_entry(entry_data: Array = []) -> void:
	var data :Dictionary = {}
	match api:
		"/farms":
			data = {
				"name": entry_data[0],
				"location": entry_data[1]
			}
		"/floors":
			data = {
				"farm_id": entry_data[0],
				"name": entry_data[1],
				"level": entry_data[2]
			}
		"/pots":
			data = {
				"floor_id": entry_data[0],
				"location_code": entry_data[1]
			}
		"/plants":
			data = {
				"pot_id": entry_data[0],
				"qr_code": str(Time.get_unix_time_from_system()),
				"species": entry_data[1],
				"variety": entry_data[2]
			}
	var body = JSON.stringify(data)
	http_request.request(
		Env.URL+Env.API+api, 
		[], 
		HTTPClient.METHOD_POST, 
		body
	)

func _on_grid_container_detail_requested(entry: Dictionary) -> void:
	print(entry)
	add_detail_screen(entry)

func _on_grid_container_table_loaded(table: Array) -> void:
	state = 1
	#print(table)

func _on_http_request_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	pass # Replace with function body.


func _on_farm_menu_button_pressed() -> void:
	add_main_screen("/farms")
	api = "/farms"


func _on_plant_menu_button_pressed() -> void:
	add_main_screen("/plants")
	api = "/plants"

func _on_calendar_menu_button_pressed() -> void:
	pass


func _on_settings_menu_button_pressed() -> void:
	pass


func _on_home_button_pressed() -> void:
	add_main_screen(api)


func _on_menu_button_pressed() -> void:
	#delete_entry()
	post_entry(["Tower_05", "Büro"])
