import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    title: 'Iniciar sesión | TecnoStock',
    loadComponent: () => import('./pages/login/login').then((m) => m.LoginPage),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/shell').then((m) => m.Shell),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        title: 'Dashboard | TecnoStock',
        data: { titulo: 'Dashboard' },
        loadComponent: () => import('./pages/dashboard/dashboard').then((m) => m.DashboardPage),
      },
      {
        path: 'productos',
        title: 'Productos | TecnoStock',
        data: { titulo: 'Productos' },
        loadComponent: () => import('./pages/productos/productos').then((m) => m.ProductosPage),
      },
      {
        path: 'categorias',
        title: 'Categorías | TecnoStock',
        data: { titulo: 'Categorías' },
        loadComponent: () => import('./pages/categorias/categorias').then((m) => m.CategoriasPage),
      },
      {
        path: 'entradas',
        title: 'Entradas | TecnoStock',
        data: { titulo: 'Registrar entrada', tipo: 'ENTRADA' },
        loadComponent: () => import('./pages/movimiento/movimiento').then((m) => m.MovimientoPage),
      },
      {
        path: 'salidas',
        title: 'Salidas | TecnoStock',
        data: { titulo: 'Registrar salida', tipo: 'SALIDA' },
        loadComponent: () => import('./pages/movimiento/movimiento').then((m) => m.MovimientoPage),
      },
      {
        path: 'historial',
        title: 'Historial | TecnoStock',
        data: { titulo: 'Historial de movimientos' },
        loadComponent: () => import('./pages/historial/historial').then((m) => m.HistorialPage),
      },
      {
        path: 'stock-bajo',
        title: 'Stock bajo | TecnoStock',
        data: { titulo: 'Productos con stock bajo' },
        loadComponent: () => import('./pages/stock-bajo/stock-bajo').then((m) => m.StockBajoPage),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
