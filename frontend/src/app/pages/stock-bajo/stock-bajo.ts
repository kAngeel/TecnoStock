import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ProductoService } from '../../services/producto.service';
import { StockBajo } from '../../core/models';
import { mensajeError } from '../../core/api';

@Component({
  selector: 'app-stock-bajo',
  imports: [
    CurrencyPipe,
    RouterLink,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  templateUrl: './stock-bajo.html',
  styleUrl: './stock-bajo.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StockBajoPage {
  private readonly productosService = inject(ProductoService);

  readonly productos = signal<StockBajo[]>([]);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);

  readonly totalFaltante = computed(() =>
    this.productos().reduce((total, producto) => total + producto.faltante, 0),
  );

  readonly valorReposicion = computed(() =>
    this.productos().reduce(
      (total, producto) => total + producto.faltante * producto.precio_compra,
      0,
    ),
  );

  readonly sinStock = computed(
    () => this.productos().filter((producto) => producto.stock === 0).length,
  );

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);

    this.productosService.stockBajo().subscribe({
      next: (productos) => {
        this.productos.set(productos);
        this.cargando.set(false);
      },
      error: (error: unknown) => {
        this.error.set(mensajeError(error));
        this.cargando.set(false);
      },
    });
  }

  porcentaje(producto: StockBajo): number {
    if (producto.stock_minimo <= 0) {
      return 0;
    }
    return Math.min(100, Math.round((producto.stock / producto.stock_minimo) * 100));
  }
}
