from flask import Flask, render_template, request, redirect, url_for
from database import get_connection

app = Flask(__name__)

@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            terrariums.id,
            terrariums.name,
            terrariums.description,
            terrariums.arduino_id,
            presets.name
        FROM terrariums
        LEFT JOIN presets ON terrariums.preset_id = presets.id
        ORDER BY terrariums.id ASC
    """)

    terrariums = cursor.fetchall()
    conn.close()

    return render_template("index.html", terrariums=terrariums)

@app.route("/terrarium/<int:terrarium_id>")
def terrarium_detail(terrarium_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            terrariums.id,
            terrariums.name,
            terrariums.description,
            terrariums.arduino_id,
            presets.name,
            presets.temperature_min,
            presets.temperature_max,
            presets.humidity_min,
            presets.humidity_max,
            presets.light_min,
            presets.light_max
        FROM terrariums
        LEFT JOIN presets ON terrariums.preset_id = presets.id
        WHERE terrariums.id = ?
    """, (terrarium_id,))
    terrarium = cursor.fetchone()

    cursor.execute("""
        SELECT
            temperature,
            humidity,
            light,
            timestamp
        FROM sensor_readings
        WHERE terrarium_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (terrarium_id,))
    readings = cursor.fetchall()

    conn.close()

    return render_template(
        "terrarium_detail.html",
        terrarium=terrarium,
        readings=readings
    )

@app.route("/terrariums/add", methods=["GET", "POST"])
def add_terrarium():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        arduino_id = request.form["arduino_id"]
        preset_id = request.form["preset_id"]

        if preset_id == "":
            preset_id = None

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO terrariums (name, description, arduino_id, preset_id)
            VALUES (?, ?, ?, ?)
        """, (name, description, arduino_id, preset_id))

        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM presets
        ORDER BY name ASC
    """)
    presets = cursor.fetchall()

    conn.close()
    return render_template("add_terrarium.html", presets=presets)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)