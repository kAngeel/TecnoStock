import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  FormField,
  form,
  maxLength,
  min,
  required,
  submit,
  validate,
} from '@angular/forms/signals';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { ProductoService } from '../../services/producto.service';
import { MovimientoService } from '../../services/movimiento.service';
import { MovimientoRegistrado, Producto, TipoMovimiento } from '../../core/models';
import { mensajeError } from '../../core/api';
import { errorDe } from '../../shared/form-utils';

interface MovimientoFormModel {
  productoId: number | null;
  cantidad: number | null;
  motivo: string;
}

@Component({
  selector: 'app-movimiento',
  imports: [
    FormField,
    CurrencyPipe,
    RouterLink,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
  ],
  templateUrl: './movimiento.html',
  styleUrl: './movimiento.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MovimientoPage {
  private readonly productosService = inject(ProductoService);
  private readonly movimientosService = inject(MovimientoService);
  private readonly route = inject(ActivatedRoute);

  readonly tipo: TipoMovimiento =
    (this.route.snapshot.data['tipo'] as TipoMovimiento | undefined) ?? 'ENTRADA';
  readonly esEntrada = this.tipo === 'ENTRADA';
  readonly titulo = this.esEntrada ? 'Registrar entrada' : 'Registrar salida';
  readonly subtitulo = this.esEntrada
    ? 'Incrementa el stock de un producto. El movimiento queda registrado en el historial.'
    : 'Disminuye el stock de un producto. No se permite retirar más unidades de las disponibles.';
  readonly etiquetaCantidad = this.esEntrada ? 'Unidades que ingresan' : 'Unidades que salen';
  readonly motivoSugerido = this.esEntrada ? 'Compra a proveedor' : 'Venta al cliente';

  readonly productos = signal<Producto[]>([]);
  readonly busqueda = signal('');
  readonly cargandoProductos = signal(true);
  readonly errorProductos = signal<string | null>(null);

  readonly modelo = signal<MovimientoFormModel>({
    productoId: null,
    cantidad: null,
    motivo: '',
  });

  readonly formulario = form(this.modelo, (campo) => {
    required(campo.productoId, { message: 'Seleccione un producto.' });

    required(campo.cantidad, { message: 'Indique la cantidad.' });
    min(campo.cantidad, 1, { message: 'La cantidad debe ser mayor que cero.' });
    validate(campo.cantidad, ({ value }) => {
      const cantidad = value();
      if (cantidad === null) {
        return undefined;
      }
      if (!Number.isInteger(cantidad)) {
        return { kind: 'entero', message: 'La cantidad debe ser un número entero.' };
      }
      const disponible = this.stockDisponible();
      if (!this.esEntrada && disponible !== null && cantidad > disponible) {
        return {
          kind: 'stock',
          message: `Solo hay ${disponible} unidades disponibles de este producto.`,
        };
      }
      return undefined;
    });

    required(campo.motivo, { message: 'El motivo es obligatorio.' });
    maxLength(campo.motivo, 200, {
      message: 'El motivo admite como máximo 200 caracteres.',
    });
  });

  readonly registrando = signal(false);
  readonly error = signal<string | null>(null);
  readonly resultado = signal<MovimientoRegistrado | null>(null);

  readonly productoSeleccionado = computed<Producto | null>(() => {
    const id = this.modelo().productoId;
    if (id === null) {
      return null;
    }
    return this.productos().find((producto) => producto.producto_id === id) ?? null;
  });

  readonly stockDisponible = computed<number | null>(() => {
    const producto = this.productoSeleccionado();
    return producto ? producto.stock : null;
  });

  readonly stockProyectado = computed<number | null>(() => {
    const producto = this.productoSeleccionado();
    const cantidad = this.modelo().cantidad;
    if (!producto || cantidad === null || !Number.isInteger(cantidad)) {
      return null;
    }
    return this.esEntrada ? producto.stock + cantidad : producto.stock - cantidad;
  });

  readonly productosFiltrados = computed(() => {
    const texto = this.busqueda().trim().toLowerCase();
    if (!texto) {
      return this.productos();
    }
    return this.productos().filter(
      (producto) =>
        producto.codigo.toLowerCase().includes(texto) ||
        producto.nombre.toLowerCase().includes(texto),
    );
  });

  errorDe = errorDe;

  constructor() {
    this.cargarProductos();
  }

  cargarProductos(): void {
    this.cargandoProductos.set(true);
    this.errorProductos.set(null);

    this.productosService.listar({ soloActivos: true }).subscribe({
      next: (productos) => {
        this.productos.set(productos);
        this.cargandoProductos.set(false);
        this.preseleccionar(productos);
      },
      error: (error: unknown) => {
        this.errorProductos.set(mensajeError(error));
        this.cargandoProductos.set(false);
      },
    });
  }

  private preseleccionar(productos: Producto[]): void {
    const solicitado = Number(this.route.snapshot.queryParamMap.get('producto'));
    if (!solicitado || !Number.isInteger(solicitado)) {
      return;
    }
    const existe = productos.some((producto) => producto.producto_id === solicitado);
    if (existe && this.modelo().productoId === null) {
      this.modelo.update((valor) => ({ ...valor, productoId: solicitado }));
    }
  }

  async registrar(event: Event): Promise<void> {
    event.preventDefault();
    this.error.set(null);
    this.resultado.set(null);

    await submit(this.formulario, {
      action: async () => {
        const datos = this.modelo();
        if (datos.productoId === null || datos.cantidad === null) {
          return;
        }

        this.registrando.set(true);
        try {
          const payload = {
            producto_id: datos.productoId,
            cantidad: datos.cantidad,
            motivo: datos.motivo.trim(),
          };

          const registrado = await new Promise<MovimientoRegistrado>((resolve, reject) => {
            const peticion = this.esEntrada
              ? this.movimientosService.registrarEntrada(payload)
              : this.movimientosService.registrarSalida(payload);
            peticion.subscribe({ next: resolve, error: reject });
          });

          this.resultado.set(registrado);
          this.actualizarStock(registrado);

          this.formulario().reset();
          this.modelo.set({
            productoId: registrado.producto_id,
            cantidad: null,
            motivo: '',
          });
        } catch (error: unknown) {
          this.error.set(mensajeError(error, 'No se pudo registrar el movimiento.'));
        } finally {
          this.registrando.set(false);
        }
      },
    });
  }

  private actualizarStock(movimiento: MovimientoRegistrado): void {
    this.productos.update((productos) =>
      productos.map((producto) =>
        producto.producto_id === movimiento.producto_id
          ? {
              ...producto,
              stock: movimiento.stock_posterior,
              valor_inventario:
                Math.round(movimiento.stock_posterior * producto.precio_compra * 100) / 100,
            }
          : producto,
      ),
    );
  }

  descartarResultado(): void {
    this.resultado.set(null);
  }

  usarMotivo(): void {
    this.modelo.update((valor) => ({ ...valor, motivo: this.motivoSugerido }));
  }
}
