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
import json

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
metrics.info('app_info', 'Product Service', version='1.0.0')

# OpenTelemetry 설정
resource = Resource(attributes={
    SERVICE_NAME: "product-service"
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

# 제품 데이터 (데모용 인메모리 저장소)
products = [
    {"id": "product1", "name": "Product 1", "price": 10.99},
    {"id": "product2", "name": "Product 2", "price": 29.99},
    {"id": "product3", "name": "Product 3", "price": 5.49}
]

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "UP"})

@app.route('/products', methods=['GET'])
def get_products():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_all_products"):
        logger.info("Fetching all products")
        return jsonify(products)

@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_product_by_id") as span:
        span.set_attribute("product.id", product_id)
        logger.info(f"Fetching product with ID: {product_id}")
        
        product = next((p for p in products if p["id"] == product_id), None)
        if product:
            return jsonify(product)
        else:
            logger.error(f"Product not found: {product_id}")
            return jsonify({"error": "Product not found"}), 404

@app.route('/products', methods=['POST'])
def create_product():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("create_product"):
        data = request.json
        if not data or not all(key in data for key in ("name", "price")):
            logger.error("Invalid product data")
            return jsonify({"error": "Invalid product data"}), 400
        
        product = {
            "id": str(uuid.uuid4()),
            "name": data["name"],
            "price": data["price"]
        }
        products.append(product)
        logger.info(f"Created new product: {product['id']}")
        return jsonify(product), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8081)))