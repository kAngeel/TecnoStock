import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { environment } from '../../environments/environment';
import { ProductoService } from './producto.service';

describe('ProductoService', () => {
  let servicio: ProductoService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    servicio = TestBed.inject(ProductoService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('envía los filtros solo cuando tienen valor', () => {
    servicio.listar({ busqueda: '  laptop  ', categoriaId: 3, soloActivos: false }).subscribe();

    const peticion = http.expectOne((req) => req.url === `${environment.apiUrl}/productos`);

    expect(peticion.request.params.get('busqueda')).toBe('laptop');
    expect(peticion.request.params.get('categoria_id')).toBe('3');
    expect(peticion.request.params.get('solo_activos')).toBe('false');
    peticion.flush([]);
  });

  it('omite parámetros vacíos', () => {
    servicio.listar({ busqueda: '   ', categoriaId: null }).subscribe();

    const peticion = http.expectOne((req) => req.url === `${environment.apiUrl}/productos`);

    expect(peticion.request.params.has('busqueda')).toBe(false);
    expect(peticion.request.params.has('categoria_id')).toBe(false);
    expect(peticion.request.params.has('solo_activos')).toBe(false);
    peticion.flush([]);
  });

  it('usa los endpoints de stock bajo y valor de inventario', () => {
    servicio.stockBajo().subscribe();
    http.expectOne(`${environment.apiUrl}/productos/stock-bajo`).flush([]);

    servicio.valorInventario().subscribe();
    http
      .expectOne(`${environment.apiUrl}/productos/valor-inventario`)
      .flush({ valor_inventario: 0 });
  });

  it('activa y desactiva productos con PATCH', () => {
    servicio.desactivar(5).subscribe();
    const desactivar = http.expectOne(`${environment.apiUrl}/productos/5/desactivar`);
    expect(desactivar.request.method).toBe('PATCH');
    desactivar.flush({});

    servicio.activar(5).subscribe();
    const activar = http.expectOne(`${environment.apiUrl}/productos/5/activar`);
    expect(activar.request.method).toBe('PATCH');
    activar.flush({});
  });
});
