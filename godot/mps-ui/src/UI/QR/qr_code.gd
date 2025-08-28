extends TextureRect

@export var qr_string := ""


@onready var http_request: HTTPRequest = $HTTPRequest

func _ready() -> void:
	# Build the Cloudflare QR URL
	var url = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=" + qr_string.uri_encode()
	http_request.request(url)
	print(url)


func _on_http_request_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	print("result: %d | response_code: %d headers: %s" % [result, response_code, headers])
	if result != OK or response_code != 200:
		push_error("QR download failed")
		return

	var img := Image.new()
	var err = img.load_png_from_buffer(body)
	if err != OK:
		push_error("QR could not be loaded")
		return

	var tex := ImageTexture.create_from_image(img)
	texture = tex
