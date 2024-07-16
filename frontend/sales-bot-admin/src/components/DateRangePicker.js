import React from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const DateRangePicker = ({ dateRange, setDateRange }) => {
  return (
    <div>
      <label>Valid From:</label>
      <DatePicker
        selected={dateRange.from}
        onChange={date => setDateRange({ ...dateRange, from: date })}
        selectsStart
        startDate={dateRange.from}
        endDate={dateRange.to}
      />
      <label>Valid To:</label>
      <DatePicker
        selected={dateRange.to}
        onChange={date => setDateRange({ ...dateRange, to: date })}
        selectsEnd
        startDate={dateRange.from}
        endDate={dateRange.to}
        minDate={dateRange.from}
      />
    </div>
  );
};

export default DateRangePicker;
