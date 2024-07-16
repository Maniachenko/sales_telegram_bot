import React, { useState, useEffect } from 'react';
import ShopSelector from './ShopSelector';
import DateRangePicker from './DateRangePicker';

const EditModal = ({ pdf, onClose, onSave }) => {
  const [shopName, setShopName] = useState(pdf.shop_name);
  const [dateRange, setDateRange] = useState({
    from: new Date(pdf.valid_from),
    to: new Date(pdf.valid_to)
  });
  const [file, setFile] = useState(null);
  const [shops, setShops] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/shops')
      .then(response => response.json())
      .then(data => setShops(data))
      .catch(error => console.error('Error fetching shops:', error));
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSave = () => {
    const updatedPdf = {
      ...pdf,
      shop_name: shopName,
      valid_from: dateRange.from.toISOString().split('T')[0],
      valid_to: dateRange.to.toISOString().split('T')[0],
      file: file
    };
    onSave(updatedPdf);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Edit PDF Details</h2>
        <ShopSelector shops={shops} onSelectShop={setShopName} selectedShop={shopName} />
        <DateRangePicker dateRange={dateRange} setDateRange={setDateRange} />
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleSave}>Save</button>
        <button onClick={onClose}>Cancel</button>
      </div>
    </div>
  );
};

export default EditModal;
