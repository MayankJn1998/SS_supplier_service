# supplier_service.py
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
import logging

app = Flask(__name__)

# Configuration - Load from environment variables, good for Docker/K8s
app.config['MYSQL_HOST'] = 'mysql'  # IMPORTANT: Use 'mysql' service name in Kubernetes
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'  #  Change this!  Use a Kubernetes secret.
app.config['MYSQL_DB'] = 'suppliers_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to initialize database - create table if not exists.
def init_db():
    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                contact_person VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(20),
                address VARCHAR(255)
            )
        """)
        conn.commit()
        cursor.close()
        logger.info("Database table 'suppliers' created or already exists.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

# Initialize the database when the app starts
with app.app_context():
    init_db()

def get_db_connection():
    """
    Helper function to get a database connection.
    """
    try:
        if not mysql.connection.is_connected():
            mysql.connection.connect()  # Re-establish the connection
        return mysql.connection
    except Exception as e:
        logger.error(f"Error getting database connection: {e}")
        return None

def handle_db_error(e):
    """
    Helper function to handle database errors.
    """
    logger.error(f"Database error: {e}")
    return jsonify({"error": "Database error"}), 500


@app.route('/suppliers', methods=['GET'])
def get_suppliers():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM suppliers")
        suppliers = cursor.fetchall()
        cursor.close()
        return jsonify(suppliers), 200
    except Exception as e:
        return handle_db_error(e)

@app.route('/suppliers/<int:id>', methods=['GET'])
def get_supplier(id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE id = %s", (id,))
        supplier = cursor.fetchone()
        cursor.close()
        if supplier:
            return jsonify(supplier), 200
        else:
            return jsonify({"error": "Supplier not found"}), 404
    except Exception as e:
        return handle_db_error(e)

@app.route('/suppliers', methods=['POST'])
def create_supplier():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input.  Request body must be JSON."}), 400
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO suppliers (name, contact_person, email, phone, address)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['name'], data.get('contact_person'), data.get('email'), data.get('phone'), data.get('address')))
        conn.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        new_supplier_id = cursor.fetchone()['LAST_INSERT_ID()']
        cursor.close()
        return jsonify({"id": new_supplier_id, "message": "Supplier created successfully"}), 201
    except Exception as e:
        return handle_db_error(e)

@app.route('/suppliers/<int:id>', methods=['PUT'])
def update_supplier(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input.  Request body must be JSON."}), 400
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE suppliers SET name=%s, contact_person=%s, email=%s, phone=%s, address=%s
            WHERE id=%s
        """, (data.get('name'), data.get('contact_person'), data.get('email'), data.get('phone'), data.get('address'), id))
        conn.commit()
        cursor.close()
        return jsonify({"message": "Supplier updated successfully"}), 200
    except Exception as e:
        return handle_db_error(e)

@app.route('/suppliers/<int:id>', methods=['DELETE'])
def delete_supplier(id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        cursor.execute("DELETE FROM suppliers WHERE id=%s", (id,))
        conn.commit()
        cursor.close()
        return jsonify({"message": "Supplier deleted successfully"}), 200
    except Exception as e:
        return handle_db_error(e)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
