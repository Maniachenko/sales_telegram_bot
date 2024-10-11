import React, { useEffect, useState } from 'react';
import PdfTable from '../components/PdfTable';
import axios from 'axios';
import { Link } from 'react-router-dom';

const HomePage = () => {
  const [pdfs, setPdfs] = useState([]);

  const fetchPdfs = () => {
    axios.get('http://127.0.0.1:5000/pdfs')
      .then(response => {
        setPdfs(response.data);
      })
      .catch(error => {
        console.error('Error fetching PDFs:', error);
      });
  };

  useEffect(() => {
    fetchPdfs();
  }, []);

  return (
    <div>
      <h1>Uploaded PDFs</h1>
      <div>
        <Link to="/upload" style={{ display: 'block', marginBottom: '10px' }}>Upload New PDF</Link>
      </div>
      <PdfTable pdfs={pdfs} refreshPdfs={fetchPdfs} />
    </div>
  );
};

export default HomePage;
