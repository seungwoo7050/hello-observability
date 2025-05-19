from flask import Flask, jsonify, request
import os
import uuid
import requests
from prometheus_flask_exporter import PrometheusMetrics
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
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
metrics.info('app_info', 'Order Service', version='1.0.0')

# OpenTelemetry 설정
resource = Resource(attributes={
    SERVICE_NAME: "order-service"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_HOST", "jaeger"),
    agent_port=int(os.getenv("JAEGER_PORT", "6831")),
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Flask와 Requests 계측
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# 서비스 URL 설정
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8081")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8082")

# 주문 데이터 (데모용 인메모리 저장소)
orders = []

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "UP"})

@app.route('/orders', methods=['GET'])
def get_orders():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_all_orders"):
        logger.info("Fetching all orders")
        return jsonify(orders)

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_order_by_id") as span:
        span.set_attribute("order.id", order_id)
        logger.info(f"Fetching order with ID: {order_id}")
        
        order = next((o for o in orders if o["id"] == order_id), None)
        if order:
            return jsonify(order)
        else:
            logger.error(f"Order not found: {order_id}")
            return jsonify({"error": "Order not found"}), 404

@app.route('/orders', methods=['POST'])
def create_order():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("create_order") as span:
        data = request.json
        if not data or not all(key in data for key in ("productId", "quantity")):
            logger.error("Invalid order data")
            return jsonify({"error": "Invalid order data"}), 400
        
        product_id = data["productId"]
        quantity = data["quantity"]
        
        span.set_attribute("product.id", product_id)
        span.set_attribute("order.quantity", quantity)
        
        # 1. 제품 정보 조회
        with tracer.start_as_current_span("get_product_details") as product_span:
            try:
                logger.info(f"Fetching product details for ID: {product_id}")
                product_response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
                product_response.raise_for_status()
                product = product_response.json()
                product_span.set_attribute("product.price", product["price"])
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching product: {str(e)}")
                return jsonify({"error": f"Product service error: {str(e)}"}), 500
        
        # 2. 재고 확인
        with tracer.start_as_current_span("check_inventory") as inventory_span:
            try:
                logger.info(f"Checking inventory for product: {product_id}, quantity: {quantity}")
                inventory_check = {
                    "productId": product_id,
                    "quantity": quantity
                }
                inventory_response = requests.post(f"{INVENTORY_SERVICE_URL}/inventory/check", json=inventory_check)
                inventory_response.raise_for_status()
                inventory_result = inventory_response.json()
                
                if not inventory_result["available"]:
                    logger.warning(f"Insufficient inventory for product: {product_id}")
                    return jsonify({
                        "error": "Insufficient inventory",
                        "currentStock": inventory_result["currentStock"],
                        "requested": quantity
                    }), 400
            except requests.exceptions.RequestException as e:
                logger.error(f"Error checking inventory: {str(e)}")
                return jsonify({"error": f"Inventory service error: {str(e)}"}), 500
        
        # 3. 주문 생성
        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "productId": product_id,
            "productName": product["name"],
            "quantity": quantity,
            "unitPrice": product["price"],
            "totalPrice": product["price"] * quantity,
            "status": "CREATED"
        }
        
        orders.append(order)
        logger.info(f"Created new order: {order_id}")
        
        # 4. 재고 업데이트
        with tracer.start_as_current_span("update_inventory"):
            try:
                new_quantity = inventory_result["currentStock"] - quantity
                logger.info(f"Updating inventory for product {product_id} to {new_quantity}")
                requests.put(
                    f"{INVENTORY_SERVICE_URL}/inventory/{product_id}", 
                    json={"quantity": new_quantity}
                )
            except requests.exceptions.RequestException as e:
                logger.error(f"Error updating inventory: {str(e)}")
                # 실제 환경에서는 재고 업데이트 실패 시 보상 트랜잭션이 필요합니다
        
        return jsonify(order), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8083)))