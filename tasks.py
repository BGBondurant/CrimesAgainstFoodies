import os
import io
import base64
import random
from datetime import date

import vertexai
from flask import Blueprint, jsonify, request
from google.cloud import storage
from vertexai.preview.vision_models import ImageGenerationModel

from database import SessionLocal, DailyImage, Food, Preparation

# --- Blueprint Setup ---
tasks_bp = Blueprint('tasks_bp', __name__)

# --- Configuration ---
# IMPORTANT: Replace these with your actual GCP project and GCS bucket name.
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "your-gcs-bucket-name")

def upload_to_gcs(file_stream, filename):
    """Uploads an in-memory file stream to a GCS bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)

        # upload_from_file requires the stream to be at position 0.
        file_stream.seek(0)
        blob.upload_from_file(file_stream, content_type='image/png')

        # Make the blob publicly viewable.
        blob.make_public()

        return blob.public_url
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None

@tasks_bp.route('/generate-daily-image', methods=['POST'])
def generate_daily_image_task():
    """
    An endpoint to be triggered by an external scheduler (e.g., Google Cloud Scheduler).
    This task generates a new AI image and saves its metadata.
    """
    # Initialize Vertex AI within the request context to avoid blocking app startup.
    # This also makes it more robust in a multi-worker environment.
    try:
        vertexai.init(project=GCP_PROJECT_ID, location="us-central1")
    except Exception as e:
        # Log the error and return a helpful message.
        print(f"Failed to initialize Vertex AI: {e}")
        return jsonify({"error": "Vertex AI initialization failed. Check credentials and project settings."}), 500

    db = SessionLocal()
    try:
        # --- New 5-Step Prompt Generation ---

        # Step 1: Generate the Dish
        preps = db.query(Preparation).order_by(db.func.random()).limit(2).all()
        foods = db.query(Food).order_by(db.func.random()).limit(2).all()

        if len(preps) < 2 or len(foods) < 2:
            return jsonify({"error": "Not enough data in preparations or foods tables (requires at least 2 of each)."}), 500

        dish_title = f"{preps[0].name} {foods[0].name} and {preps[1].name} {foods[1].name}"

        # Step 2: Select a Scene Archetype
        archetypes = ["Action Scene", "Abstract/Overhead", "Surreal/Impossible"]
        chosen_archetype = random.choice(archetypes)

        # Step 3: Populate the Scene Details
        scene_details = {
            "Action Scene": {
                "Location": ["a riot clashing with police", "a high-speed car chase on a coastal highway", "a bank heist with money flying everywhere", "a chaotic kitchen during a dinner rush fire", "the deck of a ship in a perfect storm"],
                "Protagonist Action": ["is held by a stoic riot police officer on a shield", "is precariously balanced on the dashboard, held by a getaway driver", "is being presented by a terrified bank manager", "is being rescued by a chef wearing a firefighter's helmet"],
                "Background Action": ["a protestor is trying to grab it while vaulting a barricade", "a pursuing helicopter is attempting to snag it with a net", "a fellow bank robber is making a desperate lunge for it", "a burst water pipe is spraying water everywhere around the scene"],
                "Text Method": ["graffitied on a wall in the background", "spelled out by the trail of smoke from a flare", "formed by scattered documents flying through the air", "written on the cracked screen of a dropped smartphone on the ground"]
            },
            "Abstract/Overhead": {
                "Location": ["a bed of black volcanic sand", "a surface of cracked, parched earth", "a motherboard with glowing circuits", "a luxurious bed of crushed velvet", "an ancient, weathered stone altar"],
                "Protagonist Action": ["is meticulously arranged in a perfect geometric spiral", "is deconstructed, with its components laid out in a grid", "is presented as a single, perfect portion in the exact center", "is artfully splattered across the surface like a Jackson Pollock painting"],
                "Background Action": ["subtle wisps of colored smoke curl around the edges", "a single, perfect droplet of liquid is falling towards the dish", "the surface beneath is slowly cracking", "bioluminescent fungi are gently pulsing with light around the dish"],
                "Text Method": ["etched into the surface as if by ancient tools", "formed by the glowing pathways of the circuit board", "subtly woven into the texture of the velvet", "appears as a watermark, visible only from a certain angle"]
            },
            "Surreal/Impossible": {
                "Location": ["an upside-down forest with glowing flora", "the interior of a giant, mechanical clock", "a library where the shelves are made of flowing waterfalls", "a serene asteroid field with a nebula in the background"],
                "Protagonist Action": ["is held by a gnome wearing a suit of armor made of leaves", "is being served by a clockwork automaton with too many arms", "is floating just above the hands of a librarian made of water", "is presented on a crystal platter by an ethereal space entity"],
                "Background Action": ["stars are being born in the distant nebula", "giant clock gears are slowly turning in the background", "books are swimming like fish through the water-shelves", "the roots of the upside-down trees are dripping starlight"],
                "Text Method": ["spelled out by constellations in the night sky", "formed by the hands of the giant clock", "written in the pages of a floating, open book", "appears as shimmering, magical runes on the crystal platter"]
            }
        }

        location = random.choice(scene_details[chosen_archetype]["Location"])
        protagonist_action = random.choice(scene_details[chosen_archetype]["Protagonist Action"])
        background_action = random.choice(scene_details[chosen_archetype]["Background Action"])
        text_method = random.choice(scene_details[chosen_archetype]["Text Method"])

        # Step 4: Select Camera Directives
        shot_types = ["Extreme Close-Up, focusing on a single textural detail", "Nadir Shot (straight down), creating a flat-lay effect", "Worm's-eye View (looking straight up), making the food tower over the viewer", "Point-of-View (POV) shot, as if the viewer is about to eat it", "Dutch Angle, creating a sense of unease or chaos"]
        lenses = ["a macro lens", "a fisheye lens", "an 85mm cinematic lens", "an anamorphic lens with lens flare"]
        lighting_styles = ["harsh, direct sunlight creating hard shadows", "soft, diffused light as if on an overcast day", "dramatic, low-key noir lighting with a single light source", "eerie, colorful bioluminescent light from the environment", "warm, romantic light as if from a flickering fireplace"]

        shot_type = random.choice(shot_types)
        lens = random.choice(lenses)
        lighting_style = random.choice(lighting_styles)

        # Step 5: Assemble and Output the Final Prompt
        prompt = (
            f"{shot_type} of a gourmet dish of {dish_title}. The shot is captured on {lens}. "
            f"The setting is {location}. The dish {protagonist_action}. In the background, {background_action}. "
            f"The text '{dish_title}' is creatively integrated by being {text_method}. "
            f"The scene is lit with {lighting_style}, creating a dramatic and interesting image."
        )

        # 3. Generate Image with Vertex AI (no change to this part)
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1"
        )

        if not response or not response.images:
            return jsonify({"error": "Failed to generate image from Vertex AI."}), 500

        base64_image_data = response.images[0]._base64_string

        # 4. Process Image Data In-Memory
        image_bytes = base64.b64decode(base64_image_data)
        image_stream = io.BytesIO(image_bytes)

        # 5. Upload to Google Cloud Storage (GCS)
        today = date.today()
        filename = f"crime-{today.strftime('%Y-%m-%d')}.png"
        public_url = upload_to_gcs(image_stream, filename)

        if not public_url:
            return jsonify({"error": "Failed to upload image to GCS."}), 500

        # 6. Save Metadata to Database
        new_daily_image = DailyImage(
            generation_date=today,
            food_combination=dish_title,
            public_url=public_url
        )
        db.add(new_daily_image)
        db.commit()

        return jsonify({
            "success": True,
            "message": "Daily image generated and saved successfully.",
            "image_url": public_url,
            "food_combo": dish_title
        }), 201

    except Exception as e:
        db.rollback()
        # It's good practice to log the full error.
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500
    finally:
        db.close()
