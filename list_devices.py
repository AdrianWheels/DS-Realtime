import sounddevice as sd

print("=== DISPOSITIVOS DE ENTRADA (Micrófonos) ===")
for i, device in enumerate(sd.query_devices()):
    if device['max_input_channels'] > 0:
        print(f"  [{i}] {device['name']} - {device['max_input_channels']} canales")

print("\n=== DISPOSITIVOS DE SALIDA (Altavoces) ===")
for i, device in enumerate(sd.query_devices()):
    if device['max_output_channels'] > 0:
        print(f"  [{i}] {device['name']} - {device['max_output_channels']} canales")
