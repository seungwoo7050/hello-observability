from flask import Flask, jsonify, request
import os
import uuid
from prometheus_flask_exporter import PrometheusMetrics
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask 앱 생성
app = Flask(__name__)

# Prometheus 메트릭 설정
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Inventory Service', version='1.0.0')

# OpenTelemetry 설정
resource = Resource(attributes={
    SERVICE_NAME: "inventory-service"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_HOST", "jaeger"),
    agent_port=int(os.getenv("JAEGER_PORT", "6831")),
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Flask 계측
FlaskInstrumentor().instrument_app(app)

# 인벤토리 데이터 (데모용 인메모리 저장소)
inventory = {
    "product1": 100,
    "product2": 50,
    "product3": 75
}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "UP"})

@app.route('/inventory', methods=['GET'])
def get_inventory():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_all_inventory"):
        logger.info("Fetching all inventory")
        return jsonify(inventory)

@app.route('/inventory/<product_id>', methods=['GET'])
def get_product_inventory(product_id):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_product_inventory") as span:
        span.set_attribute("product.id", product_id)
        logger.info(f"Fetching inventory for product: {product_id}")
        
        if product_id in inventory:
            return jsonify({"productId": product_id, "quantity": inventory[product_id]})
        else:
            logger.error(f"Inventory not found for product: {product_id}")
            return jsonify({"error": "Product not found in inventory"}), 404

@app.route('/inventory/<product_id>', methods=['PUT'])
def update_inventory(product_id):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("update_inventory") as span:
        span.set_attribute("product.id", product_id)
        
        data = request.json
        if not data or "quantity" not in data:
            logger.error("Invalid inventory update data")
            return jsonify({"error": "Invalid data, quantity required"}), 400
        
        inventory[product_id] = data["quantity"]
        logger.info(f"Updated inventory for product {product_id}: {data['quantity']}")
        return jsonify({"productId": product_id, "quantity": inventory[product_id]})

@app.route('/inventory/check', methods=['POST'])
def check_inventory():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("check_inventory"):
        data = request.json
        if not data or not all(key in data for key in ("productId", "quantity")):
            logger.error("Invalid inventory check data")
            return jsonify({"error": "Invalid data"}), 400
        
        product_id = data["productId"]
        requested_quantity = data["quantity"]
        
        if product_id not in inventory:
            logger.error(f"Product not found in inventory: {product_id}")
            return jsonify({"available": False, "reason": "Product not found"}), 404
        
        available = inventory[product_id] >= requested_quantity
        logger.info(f"Inventory check for {product_id}: requested={requested_quantity}, available={available}")
        
        return jsonify({
            "productId": product_id,
            "requested": requested_quantity,
            "available": available,
            "currentStock": inventory[product_id]
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8082)))