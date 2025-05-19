# load-test.py
import requests
import random
import time
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 엔드포인트 설정
BASE_URL = "http://localhost:8080"
PRODUCT_URL = f"{BASE_URL}/api/products"
ORDER_URL = f"{BASE_URL}/api/orders"

# 부하 테스트 설정
NUM_USERS = 10  # 동시 사용자 수
TEST_DURATION = 300  # 테스트 지속 시간(초)
ERROR_RATE = 0.05  # 인위적 오류 발생 비율

def simulate_user_behavior():
    """사용자 행동 시뮬레이션"""
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < TEST_DURATION:
        try:
            # 제품 목록 조회
            response = requests.get(PRODUCT_URL)
            response.raise_for_status()
            products = response.json()
            request_count += 1
            
            if not products:
                logger.warning("No products found")
                time.sleep(1)
                continue
            
            # 무작위로 제품 상세 조회
            product_id = random.choice(products)['id']
            response = requests.get(f"{PRODUCT_URL}/{product_id}")
            response.raise_for_status()
            request_count += 1
            
            # 일부 요청에서 인위적 오류 발생
            if random.random() < ERROR_RATE:
                # 존재하지 않는 제품 ID로 요청하여 오류 발생
                requests.get(f"{PRODUCT_URL}/999999")
                request_count += 1
            
            # 무작위로 주문 생성
            if random.random() < 0.3:  # 30% 확률로 주문
                order_data = {
                    "productId": product_id,
                    "quantity": random.randint(1, 5)
                }
                response = requests.post(ORDER_URL, json=order_data)
                response.raise_for_status()
                request_count += 1
            
            # 랜덤 지연
            time.sleep(random.uniform(0.1, 2.0))
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    
    logger.info(f"User simulation completed. Total requests: {request_count}")

def main():
    logger.info(f"Starting load test with {NUM_USERS} users for {TEST_DURATION} seconds")
    
    # 여러 사용자 시뮬레이션 스레드 시작
    threads = []
    for i in range(NUM_USERS):
        thread = threading.Thread(target=simulate_user_behavior)
        threads.append(thread)
        thread.start()
        logger.info(f"Started user thread {i+1}")
    
    # 모든 스레드가 완료될 때까지 대기
    for thread in threads:
        thread.join()
    
    logger.info("Load test completed")

if __name__ == "__main__":
    main()