import os
from flask import Flask, request, send_from_directory
import json
import numpy as np
from PIL import Image
import base64
from flask_cors import CORS
import cv2
# from flask_mysqldb import MySQL

app = Flask(__name__)
CORS(app)

#app.config['MYSQL_HOST'] = 'database-gallerys.cfm6weouifji.us-east-1.rds.amazonaws.com' 
#app.config['MYSQL_USER'] = 'admin' 
#app.config['MYSQL_PASSWORD'] = 'ErHFvr3MYT52tM5E5wF4' 
#app.config['MYSQL_DB'] = 'galeria'

#app.config['MYSQL_HOST'] = 'localhost' 
#app.config['MYSQL_USER'] = 'root'
#app.config['MYSQL_PASSWORD'] = 'root2'
#app.config['MYSQL_DB'] = 'galeria'
#app.config['MYSQL_DATABASE_PORT']=3306


# mysql = MySQL(app)

# Las rutas publicas para acceder a archivos publicos, despues del /public el usuario puede buscar cualquier direccion
# Si existe, se le devuelve el archivo solicitado, sirve para acceder a las imagenes.
@app.route("/public/<path:path>")
def send_images(path):
    return send_from_directory('public', path)

# Prueba de que el servidor esta en linea
@app.route("/", methods=["GET"])
def index_route():
    return json.dumps({
        "status" : 200,
        "message" : "Hello world in mundo"
    })


## Modificar esta funcion para no usar CV2
@app.route("/image", methods=["POST"])
def image_route():
    ## Obtener imagen en base 64 y la pasamos a imagen (como archivo o conjunto de bytes)
    image64 = request.form.get("image").split(",")[1]
    image = readb64(image64)
    #image = np.array(image)

    # Aplicar las transformaciones a la imagen en color
    imagen_ecualizada = ecualizar_histograma_color(image)
    imagen_invertida = invertir_imagen_color(image)

    # Ajuste gamma con un valor de gamma de ejemplo
    gamma = 3
    imagen_gamma = ajuste_gamma_color(image, gamma)

    # Codificar las imágenes de salida a base64
    imagen_ecualizada_base64 = codificar_base64(imagen_ecualizada)
    imagen_invertida_base64 = codificar_base64(imagen_invertida)
    imagen_gamma_base64 = codificar_base64(imagen_gamma)

    return json.dumps({
        'statusCode': 200,
        'imagen_ecualizada': imagen_ecualizada_base64,
        'imagen_invertida' : imagen_invertida_base64,
        'imagen_gamma' : imagen_gamma_base64
    })

@app.route("/create_gallery", methods=["PUT"])
def create_gallery():
    try:
        # Obtenemos la informacion de la galeria desde el formulario
        galeria = request.form.get("galeria")
        descripcion = request.form.get("descripcion")
        titulos = request.form.get("titulos")
        imagenes = request.form.get("imagenes")
        descripciones_extra = request.form.get("descripciones_extra")

        # Los arreglos llegan como cadena, se convierten a json
        titulos = json.loads(titulos)
        imagenes = json.loads(imagenes)
        descripciones_extra = json.loads(descripciones_extra)

        # Declaramos el arreglo donde se almacenaran las imagenes dentro del json
        imagenes_obj_array = []

        # Recorremos los arreglos y creamos la imagen en la carpeta public/imagenes
        # Luego anexamos los datos de las imagenes al arreglo
        # En caso de que la creacion del archivo falle, no se hará el registro
        for i in range(len(titulos)):
            imagenes_obj = {}
            write_image(imagenes[i],titulos[i],i)
            imagenes_obj["image"] = f"/public/imagenes/{titulos[i]}_{i}.png"
            imagenes_obj["image_name"] = titulos[i]
            imagenes_obj["image_description"] = descripciones_extra[i]
            imagenes_obj_array.append(imagenes_obj)

        # Obtenemos el archivo json
        data = read_from_json()

        # Anexamos al final del arreglo nuestro mas reciente objeto, su id corresponde al tamaño del arreglo al momento de crearse
        data['galleries'].append({
            "idgallery" : len(data['galleries']),
            "name_gallery" : galeria,
            "gallery_description" : descripcion,
            "images" : imagenes_obj_array
        })

        # Reescribimos el json
        write_on_json(data)

        # Termina el proceso con mensaje de conclusion exitosa
        return json.dumps({
            "statusCode" : 200,
            "message" : "Galeria creada exitosamente"
        })
    except Exception as error:
        print(error)
        return json.dumps({
            "statusCode" : 500,
            "message" : "Error cargando la galeria"
        })

@app.route("/get_galleries", methods=["GET"])
def get_galleries(): 
    try: 
        # Leemos el archivo json
        data = read_from_json()
 
        # Retornamos el valor que se encuentra dentro del arreglo de galerias
        return json.dumps({ 
            "statusCode" : 200, 
            "message" : "Data successfully", 
            "data" : data["galleries"] 
        }) 
    except Exception as e: 
        print(e) 
        return json.dumps({ 
            "statusCode" : 500, 
            "message" : "Error " +  str(e), 
            "data" : []
        })
    
    
# Ahora se borra con la posicion del arreglo, no por un id, por lo que el id será dinamico ya que depende de donde se guarde
@app.route("/delete_gallery", methods=["POST"])
def delete_gallery():
    idgaleria = request.form.get("idgallery")
    # convertimos el id a int porque si no la funcion pop no hace lo que debe
    idgaleria = int(idgaleria)
    try:
        # Obtenemos el valor actual del json
        data = read_from_json()
        
        # Se agrega este recorrido por si el id no corresponde a la posicion en el arreglo
        index = -1

        for i in range(len(data['galleries'])):
            if data['galleries'][i]['idgallery'] == idgaleria:
                index = i
                break

        # Eliminamos el valor en la posicion del id
        data['galleries'].pop(index)

        # Reescribimos el json ya sin el objeto eliminado
        write_on_json(data)

        return json.dumps({
            "statusCode" : 200,
            "message" : "Data successfully",
            "data" : data['galleries']
        })
    except Exception as e:
        print(e)
        return json.dumps({ 
            "statusCode" : 500, 
            "message" : "Error " +  str(e), 
            "data" : []
        })


# Funcion para obtener la data del json
def read_from_json():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "galleries.json")
    data = json.load(open(json_url))
    return data

def write_on_json(data):
    # Se agrega este recorrido para poder re etiquetar los id de las galerias segun su orden en el arreglo
    for i in range(len(data['galleries'])):
        data['galleries'][i]['idgallery'] = i

    with open("galleries.json", "w") as f:
        json.dump(data, f)

def write_image(base_64_string, nombre, index):
    with open(f"public/imagenes/{nombre.strip()}_{index}.png", "wb") as fh:
        fh.write(base64.decodebytes(base_64_string.split(",")[1].encode()))

# reescribir para funcionar con el nuevo modelo de lectura de imagenes
def readb64(base64_string):
    decoded_data = base64.b64decode(base64_string)
    np_data = np.fromstring(decoded_data,np.uint8)
    img = cv2.imdecode(np_data,cv2.IMREAD_UNCHANGED)
    return img


def invertir_imagen_color(imagen):
    return cv2.bitwise_not(imagen)

# Función para aplicar ajuste gamma a imágenes en color
def ajuste_gamma_color(imagen, gamma):
    tabla = np.array([((i / 255.0)**gamma) * 255 for i in range(256)],dtype=np.uint8)
    return cv2.LUT(imagen, tabla)


# Función para ecualizar el histograma de cada canal
def ecualizar_histograma_color(imagen):
    canales = cv2.split(imagen)
    canales_ecualizados = [cv2.equalizeHist(canal) for canal in canales]
    return cv2.merge(canales_ecualizados)


# Función para codificar una imagen OpenCV a base64
def codificar_base64(imagen):
    # Convertir la imagen a bytes utilizando cv2.imencode
    resultado, buffer = cv2.imencode('.jpg',imagen)  # Aquí obtienes un buffer de bytes
    if not resultado:
        raise ValueError("No se pudo codificar la imagen.")  # Manejo de errores
    # Codificar el buffer de bytes a base64
    return base64.b64encode(buffer).decode('utf-8')

if __name__ == "__main__":
    app.run(host="0.0.0.0")