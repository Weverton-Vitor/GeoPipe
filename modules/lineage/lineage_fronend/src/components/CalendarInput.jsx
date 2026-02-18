import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css"; // CSS base necessário
import styles from "./CalendarInput.module.css";

export function CalendarInput({ highlightedDates, onDateChange }) {
  const [startDate, setStartDate] = useState(null);

  return (
    <div className={styles.container}>
      <DatePicker
        selected={startDate}
        onChange={(date) => {
          setStartDate(date);
          onDateChange(date);
        }}
        // Aqui entra a sua lista de datas clicáveis
        // highlightDates={highlightedDates} 
        placeholderText="Selecione uma data"
        className={styles.input} // Classe para o input
        calendarClassName={styles.calendar} // Classe para o pop-over
        // dayClassName={(date) => 
        //   highlightedDates.some(d => d.toDateString() === date.toDateString()) 
        //     ? styles.hasRun 
        //     : undefined
        // }
      />
    </div>
  );
}
