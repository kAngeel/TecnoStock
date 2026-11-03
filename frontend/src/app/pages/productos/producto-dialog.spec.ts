import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { vi } from 'vitest';

import { environment } from '../../../environments/environment';
import { Producto } from '../../core/models';
import { ProductoDialog, ProductoDialogData } from './producto-dialog';

const CATEGORIA = {
  categoria_id: 7,
  nombre: 'Componentes',
  descripcion: null,
  total_productos: 0,
};

const PRODUCTO: Producto = {
  producto_id: 42,
  codigo: 'LAP-001',
  nombre: 'Laptop de prueba',
  descripcion: 'Equipo de prueba',
  categoria_id: 7,
  categoria_nombre: 'Componentes',
  precio_compra: 10.5,
  precio_venta: 15,
  stock: 0,
  stock_minimo: 2,
  activo: true,
  fecha_creacion: '2026-01-01T00:00:00',
  fecha_actualizacion: '2026-01-01T00:00:00',
  valor_inventario: 0,
  stock_bajo: true,
};

describe('ProductoDialog', () => {
  let http: HttpTestingController;
  let cerrar: ReturnType<typeof vi.fn>;
  let datos: ProductoDialogData;

  beforeEach(() => {
    cerrar = vi.fn();
    datos = { producto: null, categorias: [CATEGORIA] };

    TestBed.configureTestingModule({
      imports: [ProductoDialog],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: MAT_DIALOG_DATA, useValue: datos },
        { provide: MatDialogRef, useValue: { close: cerrar } },
      ],
    });

    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    TestBed.resetTestingModule();
  });

  function crear(override: Partial<ProductoDialogData> = {}) {
    Object.assign(datos, override);
    return TestBed.createComponent(ProductoDialog).componentInstance;
  }

  async function esperarPeticion(url: string) {
    return vi.waitFor(() => {
      const encontradas = http.match(url);
      expect(encontradas.length).toBe(1);
      return encontradas[0];
    });
  }

  it('exige los campos obligatorios del producto', () => {
    const componente = crear();

    expect(componente.formulario.codigo().errors().length).toBeGreaterThan(0);
    expect(componente.formulario.nombre().errors().length).toBeGreaterThan(0);
    expect(componente.formulario.descripcion().errors().length).toBeGreaterThan(0);
    expect(componente.formulario.categoriaId().errors().length).toBeGreaterThan(0);
    expect(componente.formulario.precioCompra().errors().length).toBeGreaterThan(0);
    expect(componente.formulario.precioVenta().errors().length).toBeGreaterThan(0);
    expect(componente.formulario().valid()).toBe(false);
  });

  it('valida precios positivos y stock mínimo entero', () => {
    const componente = crear();

    componente.modelo.set({
      codigo: 'LAP-001',
      nombre: 'Laptop',
      descripcion: 'Equipo de prueba',
      categoriaId: 7,
      precioCompra: 0,
      precioVenta: 15,
      stockMinimo: 1.5,
    });

    const mensajesCompra = componente.formulario
      .precioCompra()
      .errors()
      .map((error) => error.message);
    expect(mensajesCompra).toContain('El precio de compra debe ser mayor que cero.');

    const mensajesStock = componente.formulario
      .stockMinimo()
      .errors()
      .map((error) => error.message);
    expect(mensajesStock).toContain('El stock mínimo debe ser un número entero.');
    expect(componente.formulario().valid()).toBe(false);
  });

  it('acepta un producto válido y muestra los errores solo al tocar el campo', () => {
    const componente = crear();

    componente.modelo.set({
      codigo: 'LAP-001',
      nombre: 'Laptop',
      descripcion: 'Equipo de prueba',
      categoriaId: 7,
      precioCompra: 10.5,
      precioVenta: 15,
      stockMinimo: 2,
    });

    expect(componente.formulario().valid()).toBe(true);
    expect(componente.errorDe(componente.formulario.codigo())).toBeNull();

    componente.modelo.update((valor) => ({ ...valor, codigo: '' }));
    componente.formulario.codigo().markAsTouched();

    expect(componente.errorDe(componente.formulario.codigo())).toBe('El código es obligatorio.');
  });

  it('registra el producto con precios redondeados y sin stock en el payload', async () => {
    const componente = crear();

    componente.modelo.set({
      codigo: ' LAP-001 ',
      nombre: ' Laptop ',
      descripcion: ' Equipo de prueba ',
      categoriaId: 7,
      precioCompra: 10.556,
      precioVenta: 15,
      stockMinimo: 2,
    });

    const guardado = componente.guardar(new Event('submit'));

    const peticion = await esperarPeticion(`${environment.apiUrl}/productos`);
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toEqual({
      codigo: 'LAP-001',
      nombre: 'Laptop',
      descripcion: 'Equipo de prueba',
      categoria_id: 7,
      precio_compra: 10.56,
      precio_venta: 15,
      stock_minimo: 2,
      activo: true,
    });
    expect(peticion.request.body.stock).toBeUndefined();

    peticion.flush(PRODUCTO);
    await guardado;
    expect(cerrar).toHaveBeenCalledWith(true);
  });

  it('actualiza un producto existente conservando su estado activo', async () => {
    const componente = crear({
      producto: { ...PRODUCTO, activo: false },
    });

    expect(componente.modelo().codigo).toBe('LAP-001');
    expect(componente.modelo().categoriaId).toBe(7);

    const guardado = componente.guardar(new Event('submit'));

    const peticion = await esperarPeticion(`${environment.apiUrl}/productos/42`);
    expect(peticion.request.method).toBe('PUT');
    expect(peticion.request.body.activo).toBe(false);

    peticion.flush(PRODUCTO);
    await guardado;
    expect(cerrar).toHaveBeenCalledWith(true);
  });

  it('muestra el mensaje de la API cuando el guardado falla', async () => {
    const componente = crear();

    componente.modelo.set({
      codigo: 'LAP-001',
      nombre: 'Laptop',
      descripcion: 'Equipo de prueba',
      categoriaId: 7,
      precioCompra: 10,
      precioVenta: 15,
      stockMinimo: 2,
    });

    const guardado = componente.guardar(new Event('submit'));

    const peticion = await esperarPeticion(`${environment.apiUrl}/productos`);
    peticion.flush(
      {
        detail: 'Ya existe un producto con el código LAP-001.',
        code: 'producto_duplicado',
      },
      { status: 409, statusText: 'Conflict' },
    );
    await guardado;

    expect(componente.error()).toBe('Ya existe un producto con el código LAP-001.');
    expect(cerrar).not.toHaveBeenCalled();
  });
});
