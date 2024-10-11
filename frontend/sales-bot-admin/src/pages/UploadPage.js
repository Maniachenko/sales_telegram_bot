import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import ShopSelector from '../components/ShopSelector';
import DateRangePicker from '../components/DateRangePicker';

const UploadPage = () => {
  const [selectedShop, setSelectedShop] = useState('');
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState('');
  const [shops, setShops] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get('http://127.0.0.1:5000/shops')
      .then(response => {
        const sortedShops = response.data.sort((a, b) => a.name.localeCompare(b.name));
        setShops(sortedShops);
      })
      .catch(error => {
        console.error('Error fetching shops:', error);
      });
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleFileUrlChange = (e) => {
    setFileUrl(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedShop || !dateRange.from || !dateRange.to || (!file && !fileUrl)) {
      setError('All fields are required');
      return;
    }

    const formatDate = (date) => {
      const offset = date.getTimezoneOffset();
      const adjustedDate = new Date(date.getTime() - (offset * 60 * 1000));
      return adjustedDate.toISOString().split('T')[0];
    }

    const formData = new FormData();
    formData.append('shop_name', selectedShop);
    formData.append('valid_from', formatDate(dateRange.from));
    formData.append('valid_to', formatDate(dateRange.to));
    if (file) {
      formData.append('file', file);
    }
    if (fileUrl) {
      formData.append('file_url', fileUrl);
    }

    axios.post('http://127.0.0.1:5000/upload', formData)
      .then(response => {
        console.log(response.data);
        setError(''); // Clear any previous errors
        window.location.href = '/'; // Navigate back to the main page
      })
      .catch(error => {
        console.error('Error uploading file:', error);
        setError('Error uploading file');
      });
  };

  return (
    <div>
      <h1>Upload Shop PDF</h1>
      <Link to="/">Back to Home</Link>
      <ShopSelector shops={shops} onSelectShop={setSelectedShop} />
      <DateRangePicker dateRange={dateRange} setDateRange={setDateRange} />
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
        <input type="file" onChange={handleFileChange} style={{ display: 'block', marginBottom: '10px' }} />
        <input
          type="text"
          placeholder="Or enter PDF URL"
          value={fileUrl}
          onChange={handleFileUrlChange}
          style={{ display: 'block', marginBottom: '10px' }}
        />
        <button type="submit" style={{ display: 'block', marginBottom: '10px' }}>Upload PDF</button>
      </form>
    </div>
  );
};

export default UploadPage;
