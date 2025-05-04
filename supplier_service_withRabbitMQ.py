# supplier_service.py
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
import pika  # For RabbitMQ
import logging
import json
import time

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
#app.config['MYSQL_HOST'] = 'mysql'
app.config['MYSQL_USER'] = 'root'
#app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_PASSWORD'] = 'root123'
app.config['MYSQL_DB'] = 'suppliers_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# RabbitMQ Configuration

# Use the service name in Kubernetes
#rabbitmq_host = 'rabbitmq'  
rabbitmq_host = 'localhost'  
rabbitmq_queue = 'new_suppliers'

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_rabbitmq():
    """
    Establishes a connection to RabbitMQ.  Handles connection errors with retry logic.
    """
    for attempt in range(5):  # Retry up to 5 times
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
            channel = connection.channel()
            channel.queue_declare(queue=rabbitmq_queue, durable=True)  # Ensure queue survives restarts
            logger.info(f"Connected to RabbitMQ on attempt {attempt+1}")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}.  Retrying in 5 seconds...")
            time.sleep(5)
    logger.error("Failed to connect to RabbitMQ after 5 attempts.  Exiting.")
    return None, None

connection, channel = connect_rabbitmq()

def init_db():
    """
    Initializes the database: creates the suppliers table if it doesn't exist.
    """
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

# Initialize the database on app startup
with app.app_context():
    init_db()

"""def get_db_connection(): #Helper function to get a database connection.

    try:
        if not mysql.connection.is_connected():
            mysql.connection.connect()  # Re-establish the connection
        return mysql.connection
    except Exception as e:
        logger.error(f"Error getting database connection: {e}")
        return None"""

def handle_db_error(e):
    """
    Helper function to handle database errors.
    """
    logger.error(f"Database error: {e}")
    return jsonify({"error": "Database error"}), 500

def publish_to_rabbitmq(message):
    """
    Publishes a message to the RabbitMQ queue.
    """
    global connection, channel  # Use the global connection and channel
    if connection is None or not connection.is_open:
        connection, channel = connect_rabbitmq()  # Reconnect if needed
        if connection is None:
            logger.error("Could not reconnect to RabbitMQ, message not sent")
            return

    try:
        channel.basic_publish(
            exchange='',
            routing_key=rabbitmq_queue,
            body=json.dumps(message),  # Convert the message to JSON
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        logger.info(f"Published message: {message} to RabbitMQ queue: {rabbitmq_queue}")
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Error publishing to RabbitMQ: {e}")
        connection, channel = connect_rabbitmq() # Attempt to reconnect
        if connection is None:
             logger.error("Failed to reconnect to RabbitMQ, message not sent")

@app.route('/suppliers', methods=['GET'])
def get_suppliers():
    """
    Retrieves all suppliers from the database.
    """
    try:
        conn = mysql.connection
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
    """
    Retrieves a single supplier from the database by ID.
    """
    try:
        conn = mysql.connection
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
    """
    Creates a new supplier in the database and publishes the new supplier data to RabbitMQ.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input.  Request body must be JSON."}), 400
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        conn = mysql.connection
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

        # Include the new supplier ID in the message
        new_supplier_data = {
            'id': new_supplier_id,
            'name': data['name'],
            'contact_person': data.get('contact_person'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'address': data.get('address')
        }
        publish_to_rabbitmq(new_supplier_data)  # Publish to RabbitMQ

        return jsonify({"id": new_supplier_id, "message": "Supplier created successfully"}), 201
    except Exception as e:
        return handle_db_error(e)

@app.route('/suppliers/<int:id>', methods=['PUT'])
def update_supplier(id):
    """
    Updates an existing supplier in the database.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input.  Request body must be JSON."}), 400
        conn = mysql.connection
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
    """
    Deletes a supplier from the database.
    """
    try:
        conn = mysql.connection
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
