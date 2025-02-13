from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import json
import os

import uuid
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.static_folder = "static"
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


@app.route("/api/artigos/id/<id>", methods=["GET"])
def get_artigo_by_id(id):
    artigo = next((a for a in artigos if a["id"] == id), None)
    if artigo:
        return jsonify(artigo)
    return make_response(jsonify({"message": "Artigo not found"}), 404)


@app.route("/api/artigos/slug/<slug>", methods=["GET"])
def get_artigo_by_slug(slug):
    artigo = next((a for a in artigos if a["slug"] == slug), None)
    if artigo:
        return jsonify(artigo)
    return make_response(jsonify({"message": "Artigo not found"}), 404)


@app.route("/api/artigos/check_slug", methods=["POST"])
def check_slug():
    try:
        data = request.get_json()
        if not data or "slug" not in data or "id" not in data:
            return make_response(jsonify({"message": "Slug and ID are required"}), 400)

        slug = data["slug"]
        artigoid = data["id"]
        slug_exists = any(
            (artigo.get("slug") == slug and artigo.get("id") != artigoid)
            for artigo in artigos
        )

        return jsonify({"exists": slug_exists}), 200

    except Exception as e:
        return make_response(
            jsonify({"message": "An error occurred", "error": str(e)}), 500
        )


@app.route("/api/artigos", methods=["POST"])
def create_artigo():
    try:
        if request.content_type.startswith("multipart/form-data"):
            form_data = request.form
            is_multipart = True
        elif request.is_json:
            form_data = request.get_json()
            is_multipart = False
        else:
            return make_response(jsonify({"message": "Unsupported content type"}), 400)

        new_artigo = {}

        new_artigo["id"] = str(uuid.uuid4())
        new_artigo["titulo"] = form_data.get("titulo")
        new_artigo["sumario"] = form_data.get("sumario")
        new_artigo["assunto"] = form_data.get("assunto")
        new_artigo["slug"] = form_data.get("slug")
        new_artigo["data"] = form_data.get("data")
        new_artigo["index"] = len(artigos) + 1

        new_artigo["autor"] = {
            "nome": form_data.get("autor[nome]"),
            "avatar": form_data.get("autor[avatar]"),
        }

        if is_multipart:
            new_artigo["texto"] = [
                form_data[key]
                for key in sorted(form_data.keys())
                if key.startswith("texto[")
            ]
        else:
            new_artigo["texto"] = form_data.get("texto", [])

        # Handle image upload (only for multipart/form-data)
        if is_multipart and "imagem" in request.files:
            image_file = request.files["imagem"]
            if image_file.filename:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image_file.save(image_path)
                new_artigo["imagem"] = f"/images/{filename}"

        artigos.append(new_artigo)

        with open("artigos.json", "w", encoding="utf-8") as f:
            json.dump(artigos, f, indent=2, ensure_ascii=False)

        return jsonify(new_artigo), 201

    except Exception as e:
        return make_response(
            jsonify({"message": "Error creating article", "error": str(e)}), 500
        )


@app.route("/api/artigos", methods=["PUT"])
def update_artigo():
    try:
        if request.content_type.startswith("multipart/form-data"):
            form_data = request.form
            is_multipart = True
        elif request.is_json:
            form_data = request.get_json()
            is_multipart = False
        else:
            return make_response(jsonify({"message": "Unsupported content type"}), 400)

        if "id" not in form_data:
            return make_response(jsonify({"message": "Article ID is required"}), 400)

        artigo_id = form_data["id"]
        updated_artigo = {}

        # Extract text fields
        updated_artigo["id"] = artigo_id
        updated_artigo["titulo"] = form_data.get("titulo", "")
        updated_artigo["sumario"] = form_data.get("sumario", "")
        updated_artigo["assunto"] = form_data.get("assunto", "")
        updated_artigo["slug"] = form_data.get("slug", "")
        updated_artigo["data"] = form_data.get("data", "")
        updated_artigo["index"] = int(form_data.get("index", 0))

        # Extract autor object
        updated_artigo["autor"] = {
            "nome": form_data.get("autor[nome]", ""),
            "avatar": form_data.get("autor[avatar]", ""),
        }

        # Extract texto array
        if is_multipart:
            updated_artigo["texto"] = [
                form_data[key]
                for key in sorted(form_data.keys())
                if key.startswith("texto[")
            ]
        else:
            updated_artigo["texto"] = form_data.get("texto", [])

        # Find and update the article
        for i, artigo in enumerate(artigos):
            if artigo["id"] == artigo_id:
                old_image_path = artigo.get("imagem", "")

                # Handle image upload (only for multipart/form-data)
                if is_multipart and "imagem" in request.files:
                    image_file = request.files["imagem"]
                    if image_file.filename:
                        filename = secure_filename(image_file.filename)
                        image_path = os.path.join(UPLOAD_FOLDER, filename)
                        image_file.save(image_path)
                        updated_artigo["imagem"] = (
                            f"/images/{filename}"  # Relative path for frontend
                        )

                        # Delete the old image if it exists
                        if old_image_path:
                            if os.path.exists(app.static_folder + old_image_path):
                                os.remove(app.static_folder + old_image_path)

                else:
                    # Keep old image path if no new image was uploaded
                    updated_artigo["imagem"] = old_image_path

                artigos[i] = updated_artigo  # Update article
                with open("artigos.json", "w", encoding="utf-8") as f:
                    json.dump(artigos, f, indent=2, ensure_ascii=False)

                return jsonify(updated_artigo)  # Return updated article

        return make_response(jsonify({"message": "Article not found"}), 404)

    except Exception as e:
        return make_response(
            jsonify({"message": "Error updating article", "error": str(e)}), 500
        )


@app.route("/api/artigos", methods=["DELETE"])
def delete_artigo():
    try:
        data = request.get_json()
        if data is None or "id" not in data:
            return make_response(jsonify({"message": "ID is required"}), 400)

        artigo_id = data["id"]

        for i, artigo in enumerate(artigos):
            if artigo["id"] == artigo_id:
                del artigos[i]

                with open("artigos.json", "w", encoding="utf-8") as f:
                    json.dump(artigos, f, indent=2, ensure_ascii=False)

                return "", 204  # 204 No Content

        return make_response(jsonify({"message": "Article not found"}), 404)

    except Exception as e:
        return make_response(jsonify({"message": "An error occurred"}), 500)


if __name__ == "__main__":
    app.run(debug=True)  # Set debug=False for production
