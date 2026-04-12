identity/       # Onboarding y Gestión de Identidad

emergencies/    # 🚨 Gestión de Emergencias y Solicitudes
 
monitoring/     # 📍 Monitoreo, Experiencia y Trazabilidad
 
assignment/     # 🧠 Procesamiento Inteligente y Asignación
 
workshops/      # ⚙️ Operación de Talleres
 
admin/          # ⚙️ Administración de la Plataforma

finance/        # 💰 Monetización y Gestión Financiera


Flujo de FastApi

Resumen visual de cómo fluye la información:
Imagina que un usuario intenta hacer Login:

El internet manda un JSON a un endpoint de 👉 presentation/routers.py.

Ese router usa a 👉 presentation/schemas.py (Serializer) para validar que el email y password lleguen bien.

El router llama a la función de 👉 application/use_cases.py (Lógica) y le dice "Por favor, autentica a este usuario".

El caso de uso usa a 👉 infrastructure/models.py (Modelos) a través de repositorios para buscar en la base de datos si el usuario existe.

El caso de uso devuelve una respuesta limpia al router, y el router se lo manda de regreso al Frontend.
