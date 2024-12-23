from datetime import datetime, timedelta
import holidays
from bookings.models import Booking
from django.core.mail import EmailMessage
from django.db.models import Sum

# Instancia de festivos en Colombia (evitamos recrearla repetidamente)
colombian_holidays = holidays.Colombia()

# Configuración de horarios
HORARIOS_SEDES = {
    1: {
        "default": [("12:00", "20:16")],  # Lunes a Domingo
    },
    2: {
        "weekdays": [("12:00", "13:16"), ("19:00", "20:16")],  # Lunes a Jueves
        "friday_saturday": [("12:00", "13:46"), ("19:00", "20:16")],  # Viernes y Sábado
        "sunday": [("11:00", "15:46")],  # Domingos
        "holiday": [("11:00", "15:46")], # Festivos
        "holiday_sunday": [("12:00", "15:31"), ("19:00", "20:16")],
    },
}

DAYS_OF_WEEK = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}

# Verifica si una fecha es festiva
def isFestivo(fecha):
    try:
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("El formato de fecha debe ser YYYY-MM-DD.")
    return fecha in colombian_holidays

def isFestivoDonmingo(fecha):
    try:
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("El formato de fecha debe ser YYYY-MM-DD.")
    return (fecha + timedelta(days=1)) in colombian_holidays

# Obtiene los horarios permitidos según la sede y fecha de reserva
def obtener_horarios_permitidos(sede_id, fecha_reserva, cantidad_personas):
    """
    Obtiene los horarios permitidos para una reserva en una sede y fecha específicas.

    :param sede_id: ID de la sede (int).
    :param fecha_reserva: Fecha de la reserva (str, formato YYYY-MM-DD).
    :return: Lista de horarios permitidos (str, formato HH:MM).
    :raises ValueError: Si los parámetros no son válidos.
    """
    
    if not isinstance(fecha_reserva, str):
        raise ValueError("La fecha de reserva debe ser una cadena en formato YYYY-MM-DD.")
    
    
        
    
    es_festivo = isFestivo(fecha_reserva)
    es_festivo_domingo = isFestivoDonmingo(fecha_reserva)
    dia_semana = datetime.strptime(fecha_reserva, "%Y-%m-%d").weekday()
    dia_nombre = DAYS_OF_WEEK[dia_semana]
    horarios = []
    rangos_horarios = []
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    horarios_permitidos = []

    # Verificar si es 25 de diciembre y 1 de enero
    year = datetime.strptime(fecha_reserva, "%Y-%m-%d").year
    if fecha_reserva in [f"{year}-12-25", f"{year}-01-01"]:
        return horarios_permitidos   

    if sede_id not in HORARIOS_SEDES:
        raise ValueError(f"La sede con ID {sede_id} no está configurada.")

    config_sede = HORARIOS_SEDES[sede_id]

    if sede_id == 1:
        rangos_horarios = config_sede["default"]
    elif sede_id == 2:
        if es_festivo:
            rangos_horarios = config_sede["holiday"]
        elif es_festivo_domingo and dia_nombre == "sunday":
            rangos_horarios = config_sede["holiday_sunday"]
        elif dia_nombre in ["monday", "tuesday", "wednesday", "thursday"]:
            rangos_horarios = config_sede["weekdays"]
        elif dia_nombre in ["friday", "saturday"]:
            rangos_horarios = config_sede["friday_saturday"]
        elif dia_nombre == "sunday":
            rangos_horarios = config_sede["sunday"]

    if fecha_reserva == fecha_hoy:
        hora_actual_aux = datetime.now().time()
        hora_actual = (datetime.now() + timedelta(minutes=((30-(hora_actual_aux.minute % 15))))).time()            
        
        for inicio, fin in rangos_horarios:
            hora_inicio = datetime.strptime(inicio, "%H:%M").time()
            hora_fin = datetime.strptime(fin, "%H:%M").time()
            
            if hora_inicio <= hora_actual:
                hora_inicio = hora_actual

            while hora_inicio < hora_fin:
                horarios.append(hora_inicio.strftime("%H:%M"))
                hora_inicio = (datetime.combine(datetime.today(), hora_inicio) + timedelta(minutes=15)).time()
    else:
        for inicio, fin in rangos_horarios:
            hora_inicio = datetime.strptime(inicio, "%H:%M").time()
            hora_fin = datetime.strptime(fin, "%H:%M").time()
            while hora_inicio < hora_fin:
                horarios.append(hora_inicio.strftime("%H:%M"))
                hora_inicio = (datetime.combine(datetime.today(), hora_inicio) + timedelta(minutes=15)).time()

    for horario in horarios:
        validador = validar_cantidad_personas(int(cantidad_personas), fecha_reserva, horario, sede_id)
        if validador:
            horarios_permitidos.append(horario)
        
    return horarios_permitidos


def convert_to_am_pm(hora):
    return datetime.strptime(hora, "%H:%M").strftime("%I:%M %p")


def convert_to_24(hora):
    return datetime.strptime(hora, "%I:%M %p").strftime("%H:%M")

# Valida la cantidad de personas permitidas
def validar_cantidad_personas(cantidad_personas, fecha_reserva, hora_reserva, sede_id):
    """
    Valida que no haya más de 30 personas en el rango de 89 minutos
    alrededor de la combinación de fecha y hora de reserva.
    
    :param cantidad_personas: Número de personas para la nueva reserva.
    :param fecha_reserva: Fecha de la reserva (str, formato YYYY-MM-DD).
    :param hora_reserva: Hora de la reserva (str, formato HH:MM).
    :return: True si es válido, False en caso contrario.
    :raises ValueError: Si los parámetros no son válidos.
    """
    if not isinstance(cantidad_personas, int) or cantidad_personas <= 0:
        raise ValueError("La cantidad de personas debe ser un número entero positivo.")
    
    try:
        fecha_hora_reserva = datetime.strptime(f"{fecha_reserva} {hora_reserva}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("La fecha y la hora deben estar en los formatos 'YYYY-MM-DD' y 'HH:MM'.")
    
    # Calcular el rango de tiempo de 105 minutos antes y después
    inicio_rango = fecha_hora_reserva - timedelta(minutes=89)
    fin_rango = fecha_hora_reserva + timedelta(minutes=89)
    
    # Filtrar reservas activas dentro del rango de tiempo
    reservas_en_rango = Booking.objects.filter(active=True,
        campus_id=sede_id,
        booking_date__range=(inicio_rango.date(), fin_rango.date()),
        booking_hour__range=(inicio_rango.time(), fin_rango.time())
    ).aggregate(Sum("people_amount"))["people_amount__sum"] or 0

    # Verificar si al agregar las nuevas personas se supera el límite de 30
    if reservas_en_rango + cantidad_personas > 30:
        return False
    
    return True

# Envía un correo electrónico de confirmación de reserva
def enviar_correo_confirmacion_reserva(correo_destinatario, nombre_destinatario, fecha_reserva, hora_reserva, sede_reserva, cantidad_personas, observaciones, estado_reserva):
    """
    Envía un correo electrónico de confirmación de reserva a un destinatario.

    :param correo_destinatario: Correo del destinatario (str).
    :param nombre_destinatario: Nombre del destinatario (str).
    :param booking_data: Datos de la reserva (dict).
    :param sede_reserva: Nombre de la sede de la reserva (str).
    :return: True si el correo se envió correctamente, False en caso contrario.
    :raises ValueError: Si los parámetros no son válidos.
    """
    
    estado_reserva_upper = str(estado_reserva).upper()
    mens_final = "¡Te esperamos!" if estado_reserva == "confirmada" else "¡Esperamos verte pronto!"

    
    mensaje_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f9f9f9; color: #333;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
            <!-- Encabezado -->
            <div style="background-color: #5B5853; color: white; padding: 20px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                <img src="https://www.limoncello.com.co/wp-content/uploads/2024/08/Limoncello-nuevo-2.png" alt="Logo de la empresa" style="width: 200px; height: auto; margin-bottom: 10px;">
                <h1 style="margin: 0; font-size: 24px;">¡RESERVA {estado_reserva_upper}!</h1>
            </div>
            
            <!-- Contenido -->
            <div style="padding: 20px;">
                <p>Hola <strong>{nombre_destinatario}</strong>,</p>
                <p>Nos complace informarte que tu reserva ha sido {estado_reserva} con éxito. A continuación, los detalles:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Sede:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{sede_reserva}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Fecha:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{fecha_reserva}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Hora:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{hora_reserva}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Cantidad de personas:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{cantidad_personas}</strong></td>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Observaciones:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{observaciones}</strong></td>
                </table>
                <p>{mens_final}</p>
            </div>
            
            <!-- Pie de página -->
            <div style="background-color: #f1f1f1; padding: 10px; text-align: center; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                <p style="margin: 0; font-size: 12px;">Este correo es generado automáticamente, por favor no responder.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asun = "¡Confirmación" if estado_reserva == "confirmada" else "Cancelación"
    asunto = f"{asun} de reserva en la sede {sede_reserva}"
    
    email = EmailMessage(
        asunto,
        mensaje_html,
        'reservas@limoncello.com.co',
        [correo_destinatario],
    )
    email.content_subtype = "html"  # Define el contenido como HTML
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False


def enviar_correo_confirmacion_reserva_sede(correo_destinatario, sede_reserva, nombre_cliente, fecha_reserva, hora_reserva, cantidad_personas, celular, observaciones, estado_reserva):
    """
    Envía un correo electrónico de confirmación de reserva a un destinatario.

    :param correo_destinatario: Correo del destinatario (str).
    :param nombre_destinatario: Nombre del destinatario (str).
    :param booking_data: Datos de la reserva (dict).
    :param sede_reserva: Nombre de la sede de la reserva (str).
    :return: True si el correo se envió correctamente, False en caso contrario.
    :raises ValueError: Si los parámetros no son válidos

    """
    
    estado_reserva_upper = str(estado_reserva).upper()
    submanager_email = 'ymra777@hotmail.com'

    
    
    mensaje_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f9f9f9; color: #333;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
            <!-- Encabezado -->
            <div style="background-color: #5B5853; color: white; padding: 20px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                <img src="https://www.limoncello.com.co/wp-content/uploads/2024/08/Limoncello-nuevo-2.png" alt="Logo de la empresa" style="width: 200px; height: auto; margin-bottom: 10px;">
                <h1 style="margin: 0; font-size: 24px;">¡RESERVA {estado_reserva_upper}!</h1>
            </div>
            
            <!-- Contenido -->
            <div style="padding: 20px;">
                <p>Hola <strong>{sede_reserva}</strong>,</p>
                <p>informamos que hay una reserva {estado_reserva} con éxito. A continuación, los detalles:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Nombre del cliente:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{nombre_cliente}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Fecha:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{fecha_reserva}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Hora:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{hora_reserva}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Cantidad de personas:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{cantidad_personas}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Celular:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{celular}</strong></td>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Observaciones:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{observaciones}</strong></td>
                    </tr>
                </table>
            </div>
            
            <!-- Pie de página -->
            <div style="background-color: #f1f1f1; padding: 10px; text-align: center; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                <p style="margin: 0; font-size: 12px;">Este correo es generado automáticamente, por favor no responder.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asun = "¡Confirmación" if estado_reserva == "confirmada" else "Cancelación"
    asunto = f"{asun} de reserva en la sede {sede_reserva}"
    
    email = EmailMessage(
        asunto,
        mensaje_html,
        'reservas@limoncello.com.co',
        [correo_destinatario, submanager_email],
    )
    email.content_subtype = "html"  # Define el contenido como HTML
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False


def enviar_correo_recuperacion_contraseña(correo_destinatario, username, new_password):
    """
    Envía un correo electrónico con una nueva contraseña generada por el sistema.

    :param correo_destinatario: Correo del destinatario (str).
    :param username: Nombre de usuario asociado a la cuenta (str).
    :return: True si el correo se envió correctamente, False en caso contrario.
    :raises ValueError: Si no se encuentra el usuario o los parámetros no son válidos.
    """
    if not isinstance(correo_destinatario, str) or not isinstance(username, str):
        raise ValueError("El correo y el nombre de usuario deben ser cadenas.")
    

    # Contenido del correo
    mensaje_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f9f9f9; color: #333;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
            <!-- Encabezado -->
            <div style="background-color: #5B5853; color: white; padding: 20px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                <img src="https://www.limoncello.com.co/wp-content/uploads/2024/08/Limoncello-nuevo-2.png" alt="Logo de la empresa" style="width: 200px; height: auto; margin-bottom: 10px;">
                <h1 style="margin: 0; font-size: 24px;">Recuperación de Contraseña</h1>
            </div>
            
            <!-- Contenido -->
            <div style="padding: 20px;">
                <p>Hola <strong>{username}</strong>,</p>
                <p>Se ha generado una nueva contraseña para tu cuenta. A continuación, los detalles:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Nueva contraseña:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{new_password}</strong></td>
                    </tr>
                </table>
                <p>Por favor, utiliza esta contraseña para acceder a tu cuenta y considera cambiarla después de iniciar sesión.</p>
            </div>
            
            <!-- Pie de página -->
            <div style="background-color: #f1f1f1; padding: 10px; text-align: center; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                <p style="margin: 0; font-size: 12px;">Este correo es generado automáticamente, por favor no responder.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = "Recuperación de Contraseña"
    
    email = EmailMessage(
        asunto,
        mensaje_html,
        'reservas@limoncello.com.co',
        [correo_destinatario],  # Destinatario(s)
    )
    email.content_subtype = "html"  # Define el contenido como HTML

    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False


def enviar_correo_confirmacion_creacion_usuario(correo_destinatario, nombre_destinatario, username, password):
    """
    Envía un correo electrónico de confirmación de creación de usuario a un destinatario.

    :param correo_destinatario: Correo del destinatario (str).
    :param nombre_destinatario: Nombre del destinatario (str).
    :param username: Nombre de usuario asociado a la cuenta (str).
    :param password: Contraseña generada para la cuenta (str).
    :return: True si el correo se envió correctamente, False en caso contrario.
    :raises ValueError: Si los parámetros no son válidos.
    """
    if not isinstance(correo_destinatario, str) or not isinstance(nombre_destinatario, str) or not isinstance(username, str) or not isinstance(password, str):
        raise ValueError("Los parámetros deben ser cadenas.")
    
    # Contenido del correo
    mensaje_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f9f9f9; color: #333;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
            <!-- Encabezado -->
            <div style="background-color: #5B5853; color: white; padding: 20px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                <img src="https://www.limoncello.com.co/wp-content/uploads/2024/08/Limoncello-nuevo-2.png" alt="Logo de la empresa" style="width: 200px; height: auto; margin-bottom: 10px;">
                <h1 style="margin: 0; font-size: 24px;">¡Bienvenido a Limoncello!</h1>
            </div>
            
            <!-- Contenido -->
            <div style="padding: 20px;">
                <p>Hola <strong>{nombre_destinatario}</strong>,</p>
                <p>Tu cuenta ha sido creada con éxito. A continuación, los detalles de inicio de sesión:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Nombre de usuario:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{username}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Contraseña:</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{password}</strong></td>
                    </tr>
                </table>
                <p>Por favor, utiliza estos datos para acceder a tu cuenta y considera cambiar la contraseña después de iniciar sesión.</p>
            </div>
            
            <!-- Pie de página -->
            <div style="background-color: #f1f1f1; padding: 10px; text-align: center; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                <p style="margin: 0; font-size: 12px;">Este correo es generado automáticamente, por favor no responder.</p>
            </div>
        </div>
    </body>
    </html>
    """

    asunto = "¡Bienvenido a Limoncello!"

    email = EmailMessage(
        asunto,
        mensaje_html,
        'reservas@limoncello.com.co',
        [correo_destinatario],
    )
    email.content_subtype = "html"  # Define el contenido como HTML

    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False
    
