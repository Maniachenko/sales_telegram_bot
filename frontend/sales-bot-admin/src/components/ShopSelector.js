import React from 'react';

const ShopSelector = ({ shops, onSelectShop }) => {
  return (
    <div>
      <label>Select Shop:</label>
      <select onChange={(e) => onSelectShop(e.target.value)}>
        <option value="">Select</option>
        {shops.map(shop => (
          <option key={shop.name} value={shop.name}>{shop.name}</option>
        ))}
      </select>
    </div>
  );
};

export default ShopSelector;
