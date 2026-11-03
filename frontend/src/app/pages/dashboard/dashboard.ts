import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormField, form, required, submit, validate } from '@angular/forms/signals';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { DashboardService } from '../../services/dashboard.service';
import { Dashboard, MovimientoPorDia } from '../../core/models';
import { mensajeError } from '../../core/api';
import { errorDe } from '../../shared/form-utils';

interface RangoModel {
  desde: string;
  hasta: string;
}

interface BarraDia extends MovimientoPorDia {
  alturaEntrada: number;
  alturaSalida: number;
}

function aIso(fecha: Date): string {
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${anio}-${mes}-${dia}`;
}

@Component({
  selector: 'app-dashboard',
  imports: [
    FormField,
    CurrencyPipe,
    DatePipe,
    DecimalPipe,
    RouterLink,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPage {
  private readonly dashboardService = inject(DashboardService);

  readonly hoy = aIso(new Date());
  readonly inicioMes = this.hoy.slice(0, 8) + '01';

  readonly modelo = signal<RangoModel>({
    desde: this.inicioMes,
    hasta: this.hoy,
  });

  readonly formulario = form(this.modelo, (campo) => {
    required(campo.desde, { message: 'Indique la fecha inicial.' });
    required(campo.hasta, { message: 'Indique la fecha final.' });
    validate(campo.hasta, ({ value }) => {
      const hasta = value();
      const desde = this.modelo().desde;
      if (!hasta || !desde || hasta >= desde) {
        return undefined;
      }
      return {
        kind: 'rango',
        message: 'La fecha final no puede ser anterior a la fecha inicial.',
      };
    });
  });

  readonly datos = signal<Dashboard | null>(null);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);

  readonly resumen = computed(() => this.datos()?.resumen ?? null);

  readonly serie = computed<BarraDia[]>(() => {
    const dias = this.datos()?.serie_diaria ?? [];
    const maximo = Math.max(1, ...dias.map((d) => Math.max(d.unidades_entrada, d.unidades_salida)));
    return dias.map((dia) => ({
      ...dia,
      alturaEntrada: Math.round((dia.unidades_entrada / maximo) * 100),
      alturaSalida: Math.round((dia.unidades_salida / maximo) * 100),
    }));
  });

  readonly maximoEntrada = computed(() =>
    Math.max(0, ...(this.datos()?.serie_diaria ?? []).map((d) => d.unidades_entrada)),
  );

  readonly maximoSalida = computed(() =>
    Math.max(0, ...(this.datos()?.serie_diaria ?? []).map((d) => d.unidades_salida)),
  );

  errorDe = errorDe;

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);

    this.dashboardService.obtener(this.modelo().desde, this.modelo().hasta).subscribe({
      next: (datos) => {
        this.datos.set(datos);
        this.cargando.set(false);
      },
      error: (error: unknown) => {
        this.error.set(mensajeError(error));
        this.cargando.set(false);
      },
    });
  }

  aplicar(event: Event): void {
    event.preventDefault();
    void submit(this.formulario, {
      action: () => {
        this.cargar();
        return Promise.resolve();
      },
    });
  }

  mesActual(): void {
    this.modelo.set({ desde: this.inicioMes, hasta: this.hoy });
    this.cargar();
  }
}
