import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../environments/environment';
import { StockBajo } from '../../core/models';
import { StockBajoPage } from './stock-bajo';

const ITEMS: StockBajo[] = [
  {
    producto_id: 1,
    codigo: 'TEC-001',
    nombre: 'Teclado mecánico',
    categoria_id: 2,
    categoria_nombre: 'Periféricos',
    stock: 1,
    stock_minimo: 5,
    faltante: 4,
    precio_compra: 50,
  },
  {
    producto_id: 2,
    codigo: 'MON-002',
    nombre: 'Monitor 24 pulgadas',
    categoria_id: 2,
    categoria_nombre: 'Periféricos',
    stock: 0,
    stock_minimo: 3,
    faltante: 3,
    precio_compra: 420,
  },
];

describe('StockBajoPage', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockBajoPage],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('consulta los productos con stock bajo al iniciar', () => {
    TestBed.createComponent(StockBajoPage);

    const peticion = http.expectOne(`${environment.apiUrl}/productos/stock-bajo`);
    expect(peticion.request.method).toBe('GET');
    peticion.flush(ITEMS);
  });

  it('calcula el faltante, los productos sin stock y el costo de reposición', () => {
    const fixture = TestBed.createComponent(StockBajoPage);

    http.expectOne(`${environment.apiUrl}/productos/stock-bajo`).flush(ITEMS);
    fixture.detectChanges();

    expect(fixture.componentInstance.totalFaltante()).toBe(7);
    expect(fixture.componentInstance.sinStock()).toBe(1);
    expect(fixture.componentInstance.valorReposicion()).toBe(4 * 50 + 3 * 420);

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Teclado mecánico');
    expect(texto).toContain('Monitor 24 pulgadas');
    expect(texto).toContain('Reponer');
  });

  it('muestra el estado vacío cuando todo el inventario está sobre el mínimo', () => {
    const fixture = TestBed.createComponent(StockBajoPage);

    http.expectOne(`${environment.apiUrl}/productos/stock-bajo`).flush([]);
    fixture.detectChanges();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Todo el inventario está por encima del mínimo');
    expect(fixture.componentInstance.productos().length).toBe(0);
  });

  it('expone el error de la API y permite reintentar', () => {
    const fixture = TestBed.createComponent(StockBajoPage);
    const componente = fixture.componentInstance;

    http
      .expectOne(`${environment.apiUrl}/productos/stock-bajo`)
      .flush(
        { detail: 'No se pudo conectar con la base de datos.' },
        { status: 500, statusText: 'Server Error' },
      );

    expect(componente.error()).toBe('No se pudo conectar con la base de datos.');
    expect(componente.cargando()).toBe(false);

    componente.cargar();
    http.expectOne(`${environment.apiUrl}/productos/stock-bajo`).flush([]);
    expect(componente.error()).toBeNull();
  });
});
