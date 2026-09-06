from fronda_bridge import FrondaBridge

bridge = FrondaBridge()
print("=== DEMOSTRACION SISTEMA MULTI-AGENTE FRONDA BRICK ===")

# 1. Chequeo de Capa 1 -> Capa 3
print("\n[1. Estado del Puente]")
health = bridge.check_health()
print(f"Estado: {health.get('status')} | URL: {health.get('url')} | Modelos: {health.get('models')}")

# 2. Invocación de Capa 2 (WSL Linux Nativo)
print("\n[2. Capa 2 - Ejecución CLI en Ubuntu]")
cli_res = bridge.run_wsl_command("uname -r && free -h | grep Mem")
print("Salida:", cli_res.get("stdout"))

# 3. Invocación de Capa 3 (Clon Cognitivo Fronda Brick v0.01)
print("\n[3. Capa 3 - Consulta a Fronda Brick]")
prompt = """
Analiza técnicamente en 3 puntos breves la siguiente función de Rust para telecomunicaciones IPv7:
pub fn parse_vpi7(packet: &[u8]) -> Result<Header, &'static str> {
    if packet.len() < 8 { return Err("packet too short"); }
    Ok(Header::from_slice(&packet[..8]))
}
"""
respuesta = bridge.ask_clone(prompt)
print("Respuesta de Fronda Brick:")
print(respuesta)
