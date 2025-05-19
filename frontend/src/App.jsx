import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 제품 목록 가져오기
    const fetchProducts = async () => {
      try {
        console.log('Fetching products from API');
        const response = await axios.get('http://localhost:8080/api/products');
        setProducts(response.data);
        console.log('Products fetched successfully');
      } catch (err) {
        setError('Failed to fetch products: ' + err.message);
        console.error('Error fetching products:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  const handleBuyClick = async (productId) => {
    try {
      console.log('Creating order for product:', productId);
      await axios.post('http://localhost:8080/api/orders', {
        productId,
        quantity: 1
      });
      alert('주문이 성공적으로 처리되었습니다!');
    } catch (err) {
      alert('주문 처리 중 오류가 발생했습니다: ' + err.message);
      console.error('Error creating order:', err);
    }
  };

  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>오류: {error}</div>;

  return (
    <div className="App">
      <header className="App-header">
        <h1>제품 목록</h1>
      </header>
      <div className="product-list">
        {products.map(product => (
          <div key={product.id} className="product-card">
            <h2>{product.name}</h2>
            <p>${product.price}</p>
            <button onClick={() => handleBuyClick(product.id)}>구매하기</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;