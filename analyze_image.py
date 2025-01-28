from PIL import Image, UnidentifiedImageError
import imghdr
import magic  # Para identificar tipos de archivos
from stegano import lsb
import os

def analyze_image(filepath):
    """
    Analiza profundamente una imagen para validar formato, detectar corrupción
    y comprobar datos ocultos (esteganografía).
    """
    try:
        # Verificar la integridad básica de la imagen con PIL
        with Image.open(filepath) as img:
            img.verify()  # Verifica que el archivo es una imagen válida

        # Validar el tipo de archivo usando libmagic
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(filepath)
        if not file_type.startswith("image/"):
            return False, "El archivo no es una imagen válida."

        # Verificar si el archivo es una imagen usando imghdr
        if not imghdr.what(filepath):
            return False, "El archivo no tiene un formato de imagen válido."

        # Validar la integridad de la imagen
        with Image.open(filepath) as img:
            img.verify()  # Verificar la integridad básica
            img.load()    # Cargar completamente la imagen

        # Buscar datos ocultos con Stegano (LSB)
        try:
            hidden_data = lsb.reveal(filepath)
            if hidden_data:
                return False, "La imagen contiene datos ocultos (esteganografía)."
        except ValueError:
            # Este error ocurre cuando no hay datos ocultos en la imagen
            pass
        except Exception as e:
            # Capturar cualquier otro error inesperado
            return False, f"Error al analizar esteganografía: {str(e)}"

        # Si pasa todas las pruebas, la imagen es válida
        return True, "La imagen es válida para el sistema."

    except (UnidentifiedImageError, IOError):
        return False, "La imagen está corrupta o no se puede procesar."
    except Exception as e:
        return False, f"Error inesperado durante el análisis: {str(e)}"
