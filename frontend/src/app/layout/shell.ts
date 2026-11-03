import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  inject,
  signal,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { BreakpointObserver } from '@angular/cdk/layout';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AuthService } from '../core/auth.service';

interface ItemMenu {
  etiqueta: string;
  ruta: string;
  icono: string;
}

@Component({
  selector: 'app-shell',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatToolbarModule,
    MatIconModule,
    MatButtonModule,
    MatListModule,
    MatMenuModule,
    MatDividerModule,
    MatTooltipModule,
  ],
  templateUrl: './shell.html',
  styleUrl: './shell.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Shell {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly breakpoint = inject(BreakpointObserver);

  readonly menu: ItemMenu[] = [
    { etiqueta: 'Dashboard', ruta: '/dashboard', icono: 'dashboard' },
    { etiqueta: 'Productos', ruta: '/productos', icono: 'inventory_2' },
    { etiqueta: 'Categorías', ruta: '/categorias', icono: 'category' },
    { etiqueta: 'Entradas', ruta: '/entradas', icono: 'south_west' },
    { etiqueta: 'Salidas', ruta: '/salidas', icono: 'north_east' },
    { etiqueta: 'Historial', ruta: '/historial', icono: 'history' },
    { etiqueta: 'Stock bajo', ruta: '/stock-bajo', icono: 'notification_important' },
  ];

  private readonly esMovil = toSignal(this.breakpoint.observe('(max-width: 960px)'), {
    initialValue: { matches: false, breakpoints: {} },
  });

  readonly modo = computed<'side' | 'over'>(() => (this.esMovil().matches ? 'over' : 'side'));
  readonly abierto = signal(true);
  readonly titulo = signal('Dashboard');

  readonly iniciales = computed(() => {
    const nombre = this.auth.nombreUsuario().trim();
    if (!nombre) return 'TS';
    const partes = nombre.split(/\s+/);
    return (partes[0][0] + (partes[1]?.[0] ?? '')).toUpperCase();
  });

  constructor() {
    effect(() => {
      // En escritorio la barra lateral queda abierta; en móvil inicia cerrada.
      this.abierto.set(!this.esMovil().matches);
    });

    this.router.events.subscribe(() => {
      const rutaActiva = this.router.routerState.snapshot.root;
      let ruta = rutaActiva.firstChild;
      while (ruta?.firstChild) {
        ruta = ruta.firstChild;
      }
      this.titulo.set((ruta?.data['titulo'] as string | undefined) ?? 'TecnoStock');
    });

    if (!this.auth.usuario()) {
      this.auth.refrescarUsuario().subscribe({ error: () => undefined });
    }
  }

  alternar(): void {
    this.abierto.update((valor) => !valor);
  }

  alNavegar(): void {
    if (this.esMovil().matches) {
      this.abierto.set(false);
    }
  }

  salir(): void {
    this.auth.cerrarSesion();
  }
}
