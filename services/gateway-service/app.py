from flask import Flask, jsonify, request, Response
import os
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
from flask_cors import CORS

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
CORS(app)  # CORS 활성화

# Prometheus 메트릭 설정
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Gateway Service', version='1.0.0')

# OpenTelemetry 설정
resource = Resource(attributes={
    SERVICE_NAME: "gateway-service"
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
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8083")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "UP"})

# 프록시 함수
def proxy_request(service_url, path, method, json=None, params=None):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(f"proxy_{method.lower()}_{path}"):
        try:
            url = f"{service_url}{path}"
            logger.info(f"Proxying {method} request to {url}")
            
            if method == 'GET':
                response = requests.get(url, params=params)
            elif method == 'POST':
                response = requests.post(url, json=json)
            elif method == 'PUT':
                response = requests.put(url, json=json)
            elif method == 'DELETE':
                response = requests.delete(url)
            else:
                return jsonify({"error": "Unsupported method"}), 400
            
            return Response(
                response.content,
                status=response.status_code,
                content_type=response.headers.get('Content-Type', 'application/json')
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Proxy error: {str(e)}")
            return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

# 제품 서비스 라우트
@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    if request.method == 'GET':
        return proxy_request(PRODUCT_SERVICE_URL, '/products', 'GET', params=request.args)
    else:  # POST
        return proxy_request(PRODUCT_SERVICE_URL, '/products', 'POST', json=request.json)

@app.route('/api/products/<product_id>', methods=['GET'])
def handle_product(product_id):
    return proxy_request(PRODUCT_SERVICE_URL, f'/products/{product_id}', 'GET')

# 인벤토리 서비스 라우트
@app.route('/api/inventory', methods=['GET'])
def handle_inventory():
    return proxy_request(INVENTORY_SERVICE_URL, '/inventory', 'GET', params=request.args)

@app.route('/api/inventory/<product_id>', methods=['GET', 'PUT'])
def handle_product_inventory(product_id):
    if request.method == 'GET':
        return proxy_request(INVENTORY_SERVICE_URL, f'/inventory/{product_id}', 'GET')
    else:  # PUT
        return proxy_request(INVENTORY_SERVICE_URL, f'/inventory/{product_id}', 'PUT', json=request.json)

# 주문 서비스 라우트
@app.route('/api/orders', methods=['GET', 'POST'])
def handle_orders():
    if request.method == 'GET':
        return proxy_request(ORDER_SERVICE_URL, '/orders', 'GET', params=request.args)
    else:  # POST
        return proxy_request(ORDER_SERVICE_URL, '/orders', 'POST', json=request.json)

@app.route('/api/orders/<order_id>', methods=['GET'])
def handle_order(order_id):
    return proxy_request(ORDER_SERVICE_URL, f'/orders/{order_id}', 'GET')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))