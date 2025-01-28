from PIL import Image, UnidentifiedImageError
import os
from stegano import lsb

class ImageSecurityAnalyzer:
    def __init__(self):
        # Firmas de archivos maliciosos conocidos
        self.malicious_signatures = [
            b'MZ',      # Ejecutable de Windows
            b'%PDF',    # PDF 
            b'<!DOCTYPE html>', # HTML
            b'<script', # Script web
            b'<?php',   # PHP
            b'#!/bin'  # Script de shell
        ]

    def _check_for_malicious_content(self, filepath):
        """
        Busca contenido malicioso en la imagen
        """
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
                
                # Verificar firmas maliciosas
                for signature in self.malicious_signatures:
                    if signature in content:
                        return False, f"Contenido malicioso detectado: {signature}"
                
                # Verificar esteganografía
                try:
                    hidden_data = lsb.reveal(filepath)
                    if hidden_data and len(hidden_data) > 10:
                        return False, "Contenido oculto detectado"
                except Exception:
                    pass
                
            return True, "Contenido seguro"
        except Exception as e:
            return False, f"Error al verificar contenido: {str(e)}"

    def _validate_image_integrity(self, filepath):
        """
        Valida la integridad de la imagen
        """
        try:
            with Image.open(filepath) as img:
                # Verificar que se pueda abrir completamente
                img.verify()
                
                # Verificaciones adicionales
                if img.format not in ['JPEG', 'PNG', 'GIF', 'BMP']:
                    return False, "Formato de imagen no soportado"
                
                # Dimensiones razonables
                width, height = img.size
                if width > 7680 or height > 4320:  # Límite 8K
                    return False, "Dimensiones de imagen excesivas"
                
                # Verificar modo de color
                if img.mode not in ['RGB', 'RGBA', 'L']:
                    return False, "Modo de color no permitido"
                
            return True, "Imagen válida"
        except UnidentifiedImageError:
            return False, "Imagen corrupta o no reconocible"
        except Exception as e:
            return False, f"Error de integridad de imagen: {str(e)}"

    def analyze_image(self, filepath):
        """
        Análisis comprehensivo de seguridad de imagen
        """
        # 1. Validar integridad de la imagen
        integrity_check, integrity_msg = self._validate_image_integrity(filepath)
        if not integrity_check:
            return False, integrity_msg

        # 2. Verificar contenido malicioso
        malicious_check, malicious_msg = self._check_for_malicious_content(filepath)
        if not malicious_check:
            return False, malicious_msg

        return True, "Imagen validada exitosamente"