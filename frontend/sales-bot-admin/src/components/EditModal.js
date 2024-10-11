import React, { useState, useEffect } from 'react';
import ShopSelector from './ShopSelector';
import DateRangePicker from './DateRangePicker';

const EditModal = ({ pdf, onClose, onSave }) => {
  // State for shop name, date range, file, and available shops
  const [shopName, setShopName] = useState(pdf.shop_name || '');
  const [dateRange, setDateRange] = useState({
    from: pdf.valid_from ? new Date(pdf.valid_from) : new Date(),
    to: pdf.valid_to ? new Date(pdf.valid_to) : new Date(),
  });
  const [file, setFile] = useState(null); // For handling file input
  const [shops, setShops] = useState([]); // List of available shops

  // Fetch available shops on component mount
  useEffect(() => {
    fetch('http://127.0.0.1:5000/shops')
      .then((response) => response.json())
      .then((data) => setShops(data))
      .catch((error) => console.error('Error fetching shops:', error));
  }, []);

  // Handle file input change
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  // Save the updated PDF metadata, including optional file upload
  const handleSave = () => {
    // Validate shopName and date range
    if (!shopName || !dateRange.from || !dateRange.to) {
      alert('Please fill out all required fields.');
      return;
    }

    // Prepare the updated PDF metadata to send back to the parent component
    const updatedPdf = {
      ...pdf, // Keep existing data
      shop_name: shopName,
      valid_from: dateRange.from.toISOString().split('T')[0], // Format date as YYYY-MM-DD
      valid_to: dateRange.to.toISOString().split('T')[0],
      file: file, // Include the file if it exists
    };

    // Call the onSave function passed from the parent component
    onSave(updatedPdf);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Edit PDF Details</h2>

        {/* Shop selector for selecting the shop name */}
        <ShopSelector shops={shops} onSelectShop={setShopName} selectedShop={shopName} />

        {/* Date range picker for valid_from and valid_to */}
        <DateRangePicker dateRange={dateRange} setDateRange={setDateRange} />

        {/* File input for updating the PDF file (optional) */}
        <div>
          <label>Upload new file (optional):</label>
          <input type="file" onChange={handleFileChange} />
        </div>

        {/* Save and Cancel buttons */}
        <div className="modal-actions">
          <button onClick={handleSave}>Save</button>
          <button onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
};

export default EditModal;
