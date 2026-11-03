import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  effect,
  inject,
  signal,
} from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { FormField, form } from '@angular/forms/signals';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ProductoService } from '../../services/producto.service';
import { CategoriaService } from '../../services/categoria.service';
import { Categoria, Producto } from '../../core/models';
import { mensajeError } from '../../core/api';
import { ConfirmDialog } from '../../shared/confirm-dialog';
import { ProductoDialog } from './producto-dialog';

interface FiltrosModel {
  busqueda: string;
  categoriaId: number | null;
  soloActivos: boolean;
}

@Component({
  selector: 'app-productos',
  imports: [
    FormField,
    CurrencyPipe,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatCheckboxModule,
    MatPaginatorModule,
    MatTooltipModule,
  ],
  templateUrl: './productos.html',
  styleUrl: './productos.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProductosPage {
  private readonly productosService = inject(ProductoService);
  private readonly categoriasService = inject(CategoriaService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly destroyRef = inject(DestroyRef);

  readonly productos = signal<Producto[]>([]);
  readonly categorias = signal<Categoria[]>([]);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);

  readonly filtros = signal<FiltrosModel>({
    busqueda: '',
    categoriaId: null,
    soloActivos: true,
  });

  readonly formulario = form(this.filtros);

  readonly pagina = signal(0);
  readonly tamano = signal(10);

  readonly visibles = computed(() => {
    const inicio = this.pagina() * this.tamano();
    return this.productos().slice(inicio, inicio + this.tamano());
  });

  readonly totalActivos = computed(
    () => this.productos().filter((producto) => producto.activo).length,
  );

  readonly valorTotal = computed(() =>
    this.productos().reduce((total, producto) => total + producto.valor_inventario, 0),
  );

  private temporizador: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    this.categoriasService.listar().subscribe({
      next: (categorias) => this.categorias.set(categorias),
      error: () => undefined,
    });

    effect(() => {
      const filtros = this.filtros();
      if (this.temporizador) {
        clearTimeout(this.temporizador);
      }
      this.temporizador = setTimeout(() => this.cargar(filtros), 300);
    });

    this.destroyRef.onDestroy(() => {
      if (this.temporizador) {
        clearTimeout(this.temporizador);
      }
    });
  }

  private cargar(filtros: FiltrosModel): void {
    this.cargando.set(true);
    this.error.set(null);

    this.productosService
      .listar({
        busqueda: filtros.busqueda,
        categoriaId: filtros.categoriaId,
        soloActivos: filtros.soloActivos,
      })
      .subscribe({
        next: (productos) => {
          this.productos.set(productos);
          this.pagina.set(0);
          this.cargando.set(false);
        },
        error: (error: unknown) => {
          this.error.set(mensajeError(error));
          this.cargando.set(false);
        },
      });
  }

  recargar(): void {
    this.cargar(this.filtros());
  }

  limpiarFiltros(): void {
    this.filtros.set({ busqueda: '', categoriaId: null, soloActivos: true });
  }

  cambiarPagina(evento: PageEvent): void {
    this.pagina.set(evento.pageIndex);
    this.tamano.set(evento.pageSize);
  }

  nuevo(): void {
    this.abrirDialogo(null);
  }

  editar(producto: Producto): void {
    this.abrirDialogo(producto);
  }

  private abrirDialogo(producto: Producto | null): void {
    const referencia = this.dialog.open(ProductoDialog, {
      width: '640px',
      maxWidth: '95vw',
      data: { producto, categorias: this.categorias() },
      autoFocus: 'first-tabbable',
    });

    referencia.afterClosed().subscribe((guardado: boolean | undefined) => {
      if (guardado) {
        this.snackBar.open(
          producto ? 'Producto actualizado correctamente.' : 'Producto registrado correctamente.',
          'Cerrar',
          { duration: 3500 },
        );
        this.recargar();
      }
    });
  }

  cambiarEstado(producto: Producto): void {
    const desactivar = producto.activo;
    const referencia = this.dialog.open(ConfirmDialog, {
      width: '430px',
      maxWidth: '95vw',
      data: {
        titulo: desactivar ? 'Desactivar producto' : 'Reactivar producto',
        mensaje: desactivar
          ? `El producto "${producto.nombre}" dejará de admitir movimientos y no aparecerá en las alertas de stock bajo. Su historial y existencias se conservan.`
          : `El producto "${producto.nombre}" volverá a admitir entradas y salidas.`,
        confirmar: desactivar ? 'Desactivar' : 'Reactivar',
        peligro: desactivar,
      },
    });

    referencia.afterClosed().subscribe((confirmado: boolean | undefined) => {
      if (!confirmado) {
        return;
      }

      const operacion = desactivar
        ? this.productosService.desactivar(producto.producto_id)
        : this.productosService.activar(producto.producto_id);

      operacion.subscribe({
        next: () => {
          this.snackBar.open(
            desactivar ? 'Producto desactivado.' : 'Producto reactivado.',
            'Cerrar',
            { duration: 3000 },
          );
          this.recargar();
        },
        error: (error: unknown) => {
          this.snackBar.open(mensajeError(error), 'Cerrar', { duration: 5000 });
        },
      });
    });
  }

  estadoStock(producto: Producto): 'bajo' | 'ok' {
    return producto.stock <= producto.stock_minimo ? 'bajo' : 'ok';
  }
}
