import { CalendarInput } from './CalendarInput';
import styles from './Header.module.css';
import { RunSelect } from './RunSelect';

export function Header({ runs, selectedRun, onChange }) {
  return (
    <header className={styles.header}>
      <div className={styles.logoContainer}>
        {/* Referência direta para a pasta public */}
        <img 
          src="/geopipe_icon.png" 
          alt="Geopipe Logo" 
          className={styles.icon} 
        />
        <span className={styles.brandName}>Geopipe</span>
      </div>
      
      <nav className={styles.nav}>
        <RunSelect
                runs={runs}
                selectedRun={selectedRun}
                onChange={onChange}
              />
              <CalendarInput></CalendarInput>
      </nav>
    </header>
  );
}
