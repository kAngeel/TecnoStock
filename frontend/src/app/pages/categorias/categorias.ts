import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormField, form, maxLength, required, submit } from '@angular/forms/signals';

import { CategoriaService } from '../../services/categoria.service';
import { Categoria, CategoriaPayload } from '../../core/models';
import { mensajeError } from '../../core/api';
import { errorDe } from '../../shared/form-utils';

interface CategoriaFormModel {
  nombre: string;
  descripcion: string;
}

@Component({
  selector: 'app-categorias',
  imports: [
    FormField,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  templateUrl: './categorias.html',
  styleUrl: './categorias.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CategoriasPage {
  private readonly categoriasService = inject(CategoriaService);

  readonly categorias = signal<Categoria[]>([]);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);

  readonly modelo = signal<CategoriaFormModel>({ nombre: '', descripcion: '' });
  readonly editando = signal<Categoria | null>(null);
  readonly guardando = signal(false);
  readonly errorFormulario = signal<string | null>(null);

  readonly formulario = form(this.modelo, (campo) => {
    required(campo.nombre, { message: 'El nombre de la categoría es obligatorio.' });
    maxLength(campo.nombre, 100, {
      message: 'El nombre admite como máximo 100 caracteres.',
    });
    maxLength(campo.descripcion, 300, {
      message: 'La descripción admite como máximo 300 caracteres.',
    });
  });

  readonly totalProductos = computed(() =>
    this.categorias().reduce((total, categoria) => total + categoria.total_productos, 0),
  );

  errorDe = errorDe;

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);

    this.categoriasService.listar().subscribe({
      next: (categorias) => {
        this.categorias.set(categorias);
        this.cargando.set(false);
      },
      error: (error: unknown) => {
        this.error.set(mensajeError(error));
        this.cargando.set(false);
      },
    });
  }

  seleccionar(categoria: Categoria): void {
    this.editando.set(categoria);
    this.errorFormulario.set(null);
    this.modelo.set({
      nombre: categoria.nombre,
      descripcion: categoria.descripcion ?? '',
    });
  }

  limpiar(): void {
    this.editando.set(null);
    this.errorFormulario.set(null);
    this.modelo.set({ nombre: '', descripcion: '' });
    this.formulario().reset();
  }

  async guardar(event: Event): Promise<void> {
    event.preventDefault();
    this.errorFormulario.set(null);

    await submit(this.formulario, {
      action: async () => {
        const datos = this.modelo();
        const payload: CategoriaPayload = {
          nombre: datos.nombre.trim(),
          descripcion: datos.descripcion.trim() || null,
        };

        this.guardando.set(true);
        try {
          const categoria = this.editando();
          await new Promise<void>((resolve, reject) => {
            const peticion = categoria
              ? this.categoriasService.actualizar(categoria.categoria_id, payload)
              : this.categoriasService.crear(payload);
            peticion.subscribe({ next: () => resolve(), error: reject });
          });

          this.limpiar();
          this.cargar();
        } catch (error: unknown) {
          this.errorFormulario.set(mensajeError(error, 'No se pudo guardar la categoría.'));
        } finally {
          this.guardando.set(false);
        }
      },
    });
  }
}
