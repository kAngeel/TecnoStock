import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import {
  FormField,
  form,
  maxLength,
  min,
  required,
  submit,
  validate,
} from '@angular/forms/signals';

import { ProductoService } from '../../services/producto.service';
import { Categoria, Producto, ProductoPayload } from '../../core/models';
import { mensajeError } from '../../core/api';
import { errorDe } from '../../shared/form-utils';

export interface ProductoDialogData {
  producto: Producto | null;
  categorias: Categoria[];
}

interface ProductoFormModel {
  codigo: string;
  nombre: string;
  descripcion: string;
  categoriaId: number | null;
  precioCompra: number | null;
  precioVenta: number | null;
  stockMinimo: number | null;
}

function modeloInicial(producto: Producto | null): ProductoFormModel {
  return {
    codigo: producto?.codigo ?? '',
    nombre: producto?.nombre ?? '',
    descripcion: producto?.descripcion ?? '',
    categoriaId: producto?.categoria_id ?? null,
    precioCompra: producto?.precio_compra ?? null,
    precioVenta: producto?.precio_venta ?? null,
    stockMinimo: producto?.stock_minimo ?? 0,
  };
}

@Component({
  selector: 'app-producto-dialog',
  imports: [
    FormField,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
  ],
  templateUrl: './producto-dialog.html',
  styleUrl: './producto-dialog.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProductoDialog {
  private readonly referencia = inject(MatDialogRef<ProductoDialog, boolean>);
  private readonly data = inject<ProductoDialogData>(MAT_DIALOG_DATA);
  private readonly productosService = inject(ProductoService);

  readonly esEdicion = this.data.producto !== null;
  readonly categorias = this.data.categorias;
  readonly guardando = signal(false);
  readonly error = signal<string | null>(null);

  readonly modelo = signal<ProductoFormModel>(modeloInicial(this.data.producto));

  readonly formulario = form(this.modelo, (campo) => {
    required(campo.codigo, { message: 'El código es obligatorio.' });
    maxLength(campo.codigo, 50, {
      message: 'El código admite como máximo 50 caracteres.',
    });

    required(campo.nombre, { message: 'El nombre es obligatorio.' });
    maxLength(campo.nombre, 150, {
      message: 'El nombre admite como máximo 150 caracteres.',
    });

    required(campo.descripcion, { message: 'La descripción es obligatoria.' });
    maxLength(campo.descripcion, 500, {
      message: 'La descripción admite como máximo 500 caracteres.',
    });

    required(campo.categoriaId, { message: 'Seleccione una categoría.' });

    required(campo.precioCompra, { message: 'Indique el precio de compra.' });
    min(campo.precioCompra, 0.01, {
      message: 'El precio de compra debe ser mayor que cero.',
    });

    required(campo.precioVenta, { message: 'Indique el precio de venta.' });
    min(campo.precioVenta, 0.01, {
      message: 'El precio de venta debe ser mayor que cero.',
    });

    required(campo.stockMinimo, { message: 'Indique el stock mínimo.' });
    min(campo.stockMinimo, 0, {
      message: 'El stock mínimo no puede ser negativo.',
    });

    validate(campo.stockMinimo, ({ value }) => {
      const stock = value();
      if (stock !== null && !Number.isInteger(stock)) {
        return {
          kind: 'entero',
          message: 'El stock mínimo debe ser un número entero.',
        };
      }
      return undefined;
    });
  });

  errorDe = errorDe;

  async guardar(event: Event): Promise<void> {
    event.preventDefault();
    this.error.set(null);

    await submit(this.formulario, {
      action: async () => {
        const datos = this.modelo();
        if (
          datos.categoriaId === null ||
          datos.precioCompra === null ||
          datos.precioVenta === null ||
          datos.stockMinimo === null
        ) {
          return;
        }

        const payload: ProductoPayload = {
          codigo: datos.codigo.trim(),
          nombre: datos.nombre.trim(),
          descripcion: datos.descripcion.trim(),
          categoria_id: datos.categoriaId,
          precio_compra: Number(datos.precioCompra.toFixed(2)),
          precio_venta: Number(datos.precioVenta.toFixed(2)),
          stock_minimo: datos.stockMinimo,
          activo: this.data.producto?.activo ?? true,
        };

        this.guardando.set(true);
        try {
          const producto = this.data.producto;
          if (producto) {
            await new Promise<void>((resolve, reject) => {
              this.productosService
                .actualizar(producto.producto_id, payload)
                .subscribe({ next: () => resolve(), error: reject });
            });
          } else {
            await new Promise<void>((resolve, reject) => {
              this.productosService
                .crear(payload)
                .subscribe({ next: () => resolve(), error: reject });
            });
          }
          this.referencia.close(true);
        } catch (error: unknown) {
          this.error.set(mensajeError(error, 'No se pudo guardar el producto.'));
        } finally {
          this.guardando.set(false);
        }
      },
    });
  }

  cancelar(): void {
    this.referencia.close(false);
  }
}
