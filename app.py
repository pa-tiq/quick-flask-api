from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import json
import os

import uuid
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.static_folder = 'static'
CORS(app)

UPLOAD_FOLDER = os.path.join(app.static_folder, "images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

# Load articles from JSON file
try:
    with open("artigos.json", "r", encoding="utf-8") as f:
        artigos = json.load(f)
except FileNotFoundError:
    artigos = []

@app.route("/api/artigos", methods=["GET"])
def get_all_artigos():
    return jsonify(artigos)

@app.route("/api/artigos/<slug>", methods=["GET"])
def get_artigo_by_slug(slug):
    artigo = next((a for a in artigos if a["slug"] == slug), None)
    if artigo:
        return jsonify(artigo)
    return make_response(jsonify({"message": "Artigo not found"}), 404)


@app.route("/api/artigos", methods=["POST"])
def create_artigo():
    try:
        new_artigo = request.get_json()
        new_artigo["id"] = str(uuid.uuid4())  # Generate unique ID
        new_artigo["index"] = len(artigos) + 1 # Generate index
        artigos.append(new_artigo)

        with open("artigos.json", "w", encoding="utf-8") as f:
            json.dump(artigos, f, indent=2, ensure_ascii=False)  # Save to JSON

        return jsonify(new_artigo), 201  # 201 Created

    except (TypeError, ValueError) as e: # Handle potential errors
        return make_response(jsonify({"message": "Invalid article data"}), 400)



@app.route("/api/artigos", methods=["PUT"])
def update_artigo():
    try:
        if "id" not in request.form:
            return make_response(jsonify({"message": "Article ID is required"}), 400)

        artigo_id = request.form["id"]
        updated_artigo = {}

        # Extract text fields
        updated_artigo["id"] = artigo_id
        updated_artigo["titulo"] = request.form.get("titulo", "")
        updated_artigo["sumario"] = request.form.get("sumario", "")
        updated_artigo["assunto"] = request.form.get("assunto", "")
        updated_artigo["slug"] = request.form.get("slug", "")
        updated_artigo["data"] = request.form.get("data", "")
        updated_artigo["index"] = int(request.form.get("index", 0))

        # Extract autor object
        updated_artigo["autor"] = {
            "nome": request.form.get("autor[nome]", ""),
            "avatar": request.form.get("autor[avatar]", ""),
        }

        # Extract texto array
        updated_artigo["texto"] = [
            request.form[key] for key in sorted(request.form.keys()) if key.startswith("texto[")
        ]

        # Handle image upload
        if "imagem" in request.files:
            image_file = request.files["imagem"]
            if image_file.filename:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image_file.save(image_path)
                updated_artigo["imagem"] = f"/static/images/{filename}"  # Relative path for frontend

        # Find and update the article
        for i, artigo in enumerate(artigos):
            if artigo["id"] == artigo_id:
                # Keep old image path if no new image was uploaded
                if "imagem" not in updated_artigo:
                    updated_artigo["imagem"] = artigo.get("imagem", "")

                artigos[i] = updated_artigo  # Update article
                with open("artigos.json", "w", encoding="utf-8") as f:
                    json.dump(artigos, f, indent=2, ensure_ascii=False)

                return jsonify(updated_artigo)  # Return updated article

        return make_response(jsonify({"message": "Article not found"}), 404)

    except Exception as e:
        return make_response(jsonify({"message": "Error updating article", "error": str(e)}), 500)


@app.route("/api/artigos", methods=["DELETE"])
def delete_artigo():
    try:
      data = request.get_json()
      if data is None or 'id' not in data:
        return make_response(jsonify({'message': 'ID is required'}), 400)

      artigo_id = data['id']

      for i, artigo in enumerate(artigos):
          if artigo['id'] == artigo_id:
              del artigos[i]

              with open("artigos.json", "w", encoding="utf-8") as f:
                  json.dump(artigos, f, indent=2, ensure_ascii=False)

              return '', 204  # 204 No Content

      return make_response(jsonify({'message': 'Article not found'}), 404)

    except Exception as e:
        return make_response(jsonify({'message': 'An error occurred'}), 500)


if __name__ == "__main__":
    app.run(debug=True)  # Set debug=False for production