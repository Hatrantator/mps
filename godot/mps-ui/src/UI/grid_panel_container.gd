extends PanelContainer

@onready var panel_name_label: Label = $VBoxContainer/HBoxContainer/PanelNameLabel
@onready var panel_id_label: Label = $VBoxContainer/HBoxContainer/PanelIDLabel
@onready var icon: TextureRect = $VBoxContainer/Icon


const HYDROPONIC_TOWER_ICONS := [
	preload("uid://drpejj2x7x342"),
	preload("uid://boovwri6puim4"),
	preload("uid://bedsu4kxqtxxk"),
	preload("uid://c870wlo3j7i5o")
	]

@export_enum( "/farms","/pots", "/plants") var api: String = "/farms"
@export var entry: Dictionary = {}

signal detail_requested(entry)

func _ready() -> void:
	if entry.is_empty():
		printerr("No Dictionary assigned to "+self.name)
		return
	setup_panel()
	
func setup_panel() -> void:
	var _name: String
	var _id: int
	var _icon :Texture2D = HYDROPONIC_TOWER_ICONS[randi_range(0,3)]
	match api:
		"/farms":
			_name = entry.name+("\n%s" % entry.location)
		"/plants":
			_name = entry.name+("sp.\n%s" % entry.species)
		"/pots":
			_name = "Pot"
	
	panel_name_label.text = _name
	panel_id_label.text = "ID: "+str(int(entry.id))
	icon.texture = _icon


func _on_gui_input(event: InputEvent) -> void:
	if event.is_action_pressed("left_mouse"):
		emit_signal("detail_requested", entry)
