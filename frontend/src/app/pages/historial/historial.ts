import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  effect,
  inject,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormField, form } from '@angular/forms/signals';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { MovimientoService } from '../../services/movimiento.service';
import { ProductoService } from '../../services/producto.service';
import { Movimiento, Producto, TipoMovimiento } from '../../core/models';
import { mensajeError } from '../../core/api';

interface FiltrosModel {
  fechaDesde: string;
  fechaHasta: string;
  productoId: number | null;
  tipo: TipoMovimiento | '';
}

function aIso(fecha: Date): string {
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${anio}-${mes}-${dia}`;
}

@Component({
  selector: 'app-historial',
  imports: [
    FormField,
    DatePipe,
    RouterLink,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatPaginatorModule,
    MatProgressBarModule,
  ],
  templateUrl: './historial.html',
  styleUrl: './historial.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HistorialPage {
  private readonly movimientosService = inject(MovimientoService);
  private readonly productosService = inject(ProductoService);
  private readonly destroyRef = inject(DestroyRef);

  readonly hoy = aIso(new Date());

  readonly filtros = signal<FiltrosModel>({
    fechaDesde: '',
    fechaHasta: '',
    productoId: null,
    tipo: '',
  });

  readonly formulario = form(this.filtros);

  readonly movimientos = signal<Movimiento[]>([]);
  readonly productos = signal<Producto[]>([]);
  readonly total = signal(0);
  readonly pagina = signal(1);
  readonly tamano = signal(10);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);

  readonly totalPaginas = signal(0);

  private temporizador: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    this.productosService.listar({ soloActivos: false }).subscribe({
      next: (productos) => this.productos.set(productos),
      error: () => undefined,
    });

    effect(() => {
      // Se leen los filtros para que el efecto reaccione a cada cambio.
      this.filtros();

      if (this.temporizador) {
        clearTimeout(this.temporizador);
      }

      this.temporizador = setTimeout(() => {
        this.pagina.set(1);
        this.cargar();
      }, 300);
    });

    this.destroyRef.onDestroy(() => {
      if (this.temporizador) {
        clearTimeout(this.temporizador);
      }
    });
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);

    const filtros = this.filtros();

    this.movimientosService
      .listar({
        fechaDesde: filtros.fechaDesde || null,
        fechaHasta: filtros.fechaHasta || null,
        productoId: filtros.productoId,
        tipo: filtros.tipo || null,
        pagina: this.pagina(),
        tamanoPagina: this.tamano(),
      })
      .subscribe({
        next: (respuesta) => {
          this.movimientos.set(respuesta.items);
          this.total.set(respuesta.total);
          this.totalPaginas.set(respuesta.total_paginas);
          this.cargando.set(false);
        },
        error: (error: unknown) => {
          this.error.set(mensajeError(error));
          this.cargando.set(false);
        },
      });
  }

  cambiarPagina(evento: PageEvent): void {
    this.pagina.set(evento.pageIndex + 1);
    this.tamano.set(evento.pageSize);
    this.cargar();
  }

  limpiar(): void {
    this.filtros.set({ fechaDesde: '', fechaHasta: '', productoId: null, tipo: '' });
  }

  rangoRapido(dias: number): void {
    const hasta = new Date();
    const desde = new Date();
    desde.setDate(desde.getDate() - (dias - 1));
    this.filtros.update((valor) => ({
      ...valor,
      fechaDesde: aIso(desde),
      fechaHasta: aIso(hasta),
    }));
  }

  mesActual(): void {
    const hoy = new Date();
    const primero = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    this.filtros.update((valor) => ({
      ...valor,
      fechaDesde: aIso(primero),
      fechaHasta: aIso(hoy),
    }));
  }
}
