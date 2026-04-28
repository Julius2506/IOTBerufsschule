from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import get_connection

app = Flask(__name__)


@app.route("/")
def index():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                terrariums.id,
                terrariums.name,
                terrariums.description,
                terrariums.arduino_id,
                presets.name,
                latest.temperature,
                latest.humidity,
                latest.light,
                latest.soil_moisture,
                latest.motion,
                latest.timestamp
                       
            FROM terrariums
            LEFT JOIN presets
                ON terrariums.preset_id = presets.id
            LEFT JOIN (
                SELECT sr1.*
                FROM sensor_readings sr1
                INNER JOIN (
                    SELECT terrarium_id, MAX(timestamp) AS max_timestamp
                    FROM sensor_readings
                    GROUP BY terrarium_id
                ) sr2
                ON sr1.terrarium_id = sr2.terrarium_id
                AND sr1.timestamp = sr2.max_timestamp
            ) AS latest
                ON terrariums.id = latest.terrarium_id
            ORDER BY terrariums.id ASC
        """)

        terrariums = cursor.fetchall()

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
            soil_moisture,
            motion,
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

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO terrariums (name, description, arduino_id, preset_id)
                VALUES (?, ?, ?, ?)
            """, (name, description, arduino_id, preset_id))

        return redirect(url_for("list_terrariums"))

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name
            FROM presets
            ORDER BY name ASC
        """)
        presets = cursor.fetchall()

    return render_template("add_terrarium.html", presets=presets)


@app.route("/terrariums")
def list_terrariums():
    with get_connection() as conn:
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
            ORDER BY terrariums.name ASC
        """)
        terrariums = cursor.fetchall()

    return render_template("terrariums.html", terrariums=terrariums)


@app.route("/terrariums/<int:terrarium_id>/edit", methods=["GET", "POST"])
def edit_terrarium(terrarium_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        if request.method == "POST":
            name = request.form["name"]
            description = request.form["description"]
            arduino_id = request.form["arduino_id"]
            preset_id = request.form["preset_id"]

            if preset_id == "":
                preset_id = None

            cursor.execute("""
                UPDATE terrariums
                SET
                    name = ?,
                    description = ?,
                    arduino_id = ?,
                    preset_id = ?
                WHERE id = ?
            """, (
                name,
                description,
                arduino_id,
                preset_id,
                terrarium_id
            ))

            return redirect(url_for("list_terrariums"))

        cursor.execute("""
            SELECT
                id,
                name,
                description,
                arduino_id,
                preset_id
            FROM terrariums
            WHERE id = ?
        """, (terrarium_id,))
        terrarium = cursor.fetchone()

        cursor.execute("""
            SELECT id, name
            FROM presets
            ORDER BY name ASC
        """)
        presets = cursor.fetchall()

    return render_template(
        "edit_terrarium.html",
        terrarium=terrarium,
        presets=presets
    )


@app.route("/terrariums/<int:terrarium_id>/delete", methods=["POST"])
def delete_terrarium(terrarium_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM sensor_readings
            WHERE terrarium_id = ?
        """, (terrarium_id,))

        cursor.execute("""
            DELETE FROM terrariums
            WHERE id = ?
        """, (terrarium_id,))

    return redirect(url_for("list_terrariums"))


@app.route("/presets/add", methods=["GET", "POST"])
def add_preset():
    if request.method == "POST":
        name = request.form["name"]
        temperature_min = request.form["temperature_min"]
        temperature_max = request.form["temperature_max"]
        humidity_min = request.form["humidity_min"]
        humidity_max = request.form["humidity_max"]
        light_min = request.form["light_min"]
        light_max = request.form["light_max"]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO presets (
                    name,
                    temperature_min,
                    temperature_max,
                    humidity_min,
                    humidity_max,
                    light_min,
                    light_max
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                temperature_min,
                temperature_max,
                humidity_min,
                humidity_max,
                light_min,
                light_max
            ))

        return redirect(url_for("list_presets"))

    return render_template("add_preset.html")


@app.route("/presets")
def list_presets():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id,
                name,
                temperature_min,
                temperature_max,
                humidity_min,
                humidity_max,
                light_min,
                light_max
            FROM presets
            ORDER BY name ASC
        """)
        presets = cursor.fetchall()

    return render_template("presets.html", presets=presets)


@app.route("/presets/<int:preset_id>/edit", methods=["GET", "POST"])
def edit_preset(preset_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        if request.method == "POST":
            name = request.form["name"]
            temperature_min = request.form["temperature_min"]
            temperature_max = request.form["temperature_max"]
            humidity_min = request.form["humidity_min"]
            humidity_max = request.form["humidity_max"]
            light_min = request.form["light_min"]
            light_max = request.form["light_max"]

            cursor.execute("""
                UPDATE presets
                SET
                    name = ?,
                    temperature_min = ?,
                    temperature_max = ?,
                    humidity_min = ?,
                    humidity_max = ?,
                    light_min = ?,
                    light_max = ?
                WHERE id = ?
            """, (
                name,
                temperature_min,
                temperature_max,
                humidity_min,
                humidity_max,
                light_min,
                light_max,
                preset_id
            ))

            return redirect(url_for("list_presets"))

        cursor.execute("""
            SELECT
                id,
                name,
                temperature_min,
                temperature_max,
                humidity_min,
                humidity_max,
                light_min,
                light_max
            FROM presets
            WHERE id = ?
        """, (preset_id,))
        preset = cursor.fetchone()

    return render_template("edit_preset.html", preset=preset)


@app.route("/presets/<int:preset_id>/delete", methods=["POST"])
def delete_preset(preset_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE terrariums
            SET preset_id = NULL
            WHERE preset_id = ?
        """, (preset_id,))

        cursor.execute("""
            DELETE FROM presets
            WHERE id = ?
        """, (preset_id,))

    return redirect(url_for("list_presets"))

@app.route("/api/terrariums")
def api_terrariums():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                terrariums.id,
                terrariums.name,
                terrariums.description,
                terrariums.arduino_id,
                presets.name,
                presets.light_min,
                presets.light_max,
                latest.temperature,
                latest.humidity,
                latest.light,
                latest.soil_moisture,
                latest.motion,
                latest.timestamp
            FROM terrariums
            LEFT JOIN presets
                ON terrariums.preset_id = presets.id
            LEFT JOIN (
                SELECT sr1.*
                FROM sensor_readings sr1
                INNER JOIN (
                    SELECT terrarium_id, MAX(timestamp) AS max_timestamp
                    FROM sensor_readings
                    GROUP BY terrarium_id
                ) sr2
                ON sr1.terrarium_id = sr2.terrarium_id
                AND sr1.timestamp = sr2.max_timestamp
            ) AS latest
                ON terrariums.id = latest.terrarium_id
            ORDER BY terrariums.id ASC
        """)

        rows = cursor.fetchall()

    terrariums = []
    for row in rows:
        terrariums.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "arduino_id": row[3],
            "preset_name": row[4],
            "light_min": row[5],
            "light_max": row[6],
            "temperature": row[7],
            "humidity": row[8],
            "light": row[9],
            "soil_moisture": row[10],
            "motion": row[11],
            "timestamp": row[12]
        })

    return jsonify(terrariums)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)