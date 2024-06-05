from flask import Flask, request
import json
import numpy as np
from PIL import Image
import base64
from flask_cors import CORS
import cv2
from flask_mysqldb import MySQL

app = Flask(__name__)
CORS(app)

#app.config['MYSQL_HOST'] = 'database-gallerys.cfm6weouifji.us-east-1.rds.amazonaws.com' 
#app.config['MYSQL_USER'] = 'admin' 
#app.config['MYSQL_PASSWORD'] = 'ErHFvr3MYT52tM5E5wF4' 
#app.config['MYSQL_DB'] = 'galeria'

app.config['MYSQL_HOST'] = 'localhost' 
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root2'
app.config['MYSQL_DB'] = 'galeria'
app.config['MYSQL_DATABASE_PORT']=3306


mysql = MySQL(app)


@app.route("/", methods=["GET"])
def index_route():
    return json.dumps({
        "status" : 200,
        "message" : "Hello world in mundo"
    })

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
        galeria = request.form.get("galeria")
        descripcion = request.form.get("descripcion")
        titulos = request.form.get("titulos")
        imagenes = request.form.get("imagenes")
        descripciones_extra = request.form.get("descripciones_extra")

        # Los arreglos llegan como cadena, se convierten a json
        titulos = json.loads(titulos)
        imagenes = json.loads(imagenes)
        descripciones_extra = json.loads(descripciones_extra)
        
        cursor = mysql.connection.cursor()
        cursor.execute('''INSERT INTO gallery (name_gallery, gallery_description) values (%s, %s)''',(galeria,descripcion))
        id_galeria = cursor.lastrowid
        mysql.connection.commit()
        cursor.close()

        cursor = mysql.connection.cursor()
        for i, titles in enumerate(titulos):
            cursor.execute("INSERT INTO images (gallery_idgallery, image_name, image_description, image) VALUES ("+str(id_galeria)+", '"+titles+"', '"+descripciones_extra[i]+"','"+imagenes[i]+"')")
            mysql.connection.commit()
            
        cursor.close()

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
        query = "SELECT * FROM gallery" 
        cursor = mysql.connection.cursor() 

        cursor.execute(query) 
        results = cursor.fetchall() 
        cursor.close() 
 
        galerias = [] 
         
        cursor = mysql.connection.cursor() 
 
        for row in results: 
            aux ={} 
            imagenes = [] 
            aux["id"] = row[0] 
            aux["name_gallery"] = row[1] 
            aux["gallery_description"] = row[2] 
            cursor.execute("SELECT * FROM images where gallery_idgallery="+str(row[0])) 
            rows = cursor.fetchall() 

            print(rows)

            for image in rows: 
                aux2 = {} 
                aux2["idimage"] = image[0] 
                aux2["image_name"] = image[2] 
                aux2["image_description"] = image[3] 
                aux2["image"] = image[4].decode('utf-8') 
                imagenes.append(aux2) 
            aux["images"] = imagenes 
            galerias.append(aux) 
 
        cursor.close() 
 
        return json.dumps({ 
            "statusCode" : 200, 
            "message" : "Data successfully", 
            "data" : galerias 
        }) 
    except Exception as e: 
        print(e) 
        return json.dumps({ 
            "statusCode" : 00, 
            "message" : "Error " +  str(e), 
            "data" : []
        })
    
@app.route("/delete_gallery", methods=["POST"])
def delete_gallery():
    idgaleria = request.form.get("idgallery")
    query = "DELETE FROM gallery where idgallery=" + str(idgaleria)
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    mysql.connection.commit()
    cursor.close()

    query = "SELECT * FROM gallery"
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()

    galerias = []
    
    cursor = mysql.connection.cursor()

    for row in results:
        aux ={}
        imagenes = []
        aux["idgallery"] = row[0]
        aux["name_gallery"] = row[1]
        aux["gallery_description"] = row[2]
        cursor.execute("SELECT * FROM images where gallery_idgallery="+str(row[0]))
        rows = cursor.fetchall()

        for image in rows:
            aux2 = {}
            aux2["idimage"] = image[0]
            aux2["image_name"] = image[2]
            aux2["image_description"] = image[3]
            aux2["image"] = image[4].decode('utf-8')
            imagenes.append(aux2)
        aux["images"] = imagenes
        galerias.append(aux)

    cursor.close()

    return json.dumps({
        "statusCode" : 200,
        "message" : "Data successfully",
        "data" : galerias
    })


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