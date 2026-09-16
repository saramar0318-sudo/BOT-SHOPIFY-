import os
import io
from PIL import Image, ImageOps

# Soporte para abrir archivos HEIC de iPhone automáticamente
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

def procesar_imagen_streamlit(img_file, es_foto_real=True, porcentaje_logo=0.20):
    """
    Toma un archivo subido en Streamlit, le aplica tu logo.png y la insignia foto_real.png
    usando los archivos que tienes en la raíz del proyecto.
    """
    try:
        # Abrir imagen desde el archivo subido en memoria
        img_file.seek(0)
        img = Image.open(img_file)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGBA")
        
        ancho_img, alto_img = img.size

        # --- 1. APLICAR LOGO (Esquina superior derecha) ---
        ruta_logo = "logo.png"
        if os.path.exists(ruta_logo):
            logo = Image.open(ruta_logo).convert("RGBA")
            ancho_logo = int(ancho_img * porcentaje_logo)
            proporcion_logo = ancho_logo / float(logo.size[0])
            alto_logo = int(float(logo.size[1]) * float(proporcion_logo))
            logo = logo.resize((ancho_logo, alto_logo), Image.Resampling.LANCZOS)

            margen_x = int(ancho_img * 0.005)
            margen_y = int(alto_img * 0.005)
            pos_x = ancho_img - ancho_logo - margen_x
            pos_y = margen_y
            
            img.paste(logo, (pos_x, pos_y), logo)
        else:
            print("[AVISO] No se encontró 'logo.png' en la raíz.")

        # --- 2. APLICAR INSIGNIA FOTO REAL (Esquina inferior izquierda) ---
        if es_foto_real:
            ruta_badge = "foto_real.png"
            if os.path.exists(ruta_badge):
                badge = Image.open(ruta_badge).convert("RGBA")
                ancho_badge = int(ancho_img * 0.18)
                proporcion_badge = ancho_badge / float(badge.size[0])
                alto_badge = int(float(badge.size[1]) * float(proporcion_badge))
                badge = badge.resize((ancho_badge, alto_badge), Image.Resampling.LANCZOS)

                margen_x = int(ancho_img * 0.005)
                margen_y = int(alto_img * 0.005)
                pos_x_badge = margen_x
                pos_y_badge = alto_img - alto_badge - margen_y
                
                img.paste(badge, (pos_x_badge, pos_y_badge), badge)
            else:
                print("[AVISO] No se encontró 'foto_real.png' en la raíz.")

        # Convertir a RGB y guardar en un búfer listo para enviar a Shopify
        output_buffer = io.BytesIO()
        img.convert("RGB").save(output_buffer, format="JPEG", quality=95)
        output_buffer.seek(0)
        return output_buffer

    except Exception as e:
        raise ValueError(f"Error procesando la imagen con marca de agua: {e}")