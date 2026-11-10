import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { FormField, form, required, minLength, submit } from '@angular/forms/signals';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { firstValueFrom } from 'rxjs';

import { AuthService } from '../../core/auth.service';
import { mensajeErrorLogin } from '../../core/api';
import { errorDe } from '../../shared/form-utils';

interface LoginModel {
  nombreUsuario: string;
  contrasena: string;
}

@Component({
  selector: 'app-login',
  imports: [
    FormField,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
  ],
  templateUrl: './login.html',
  styleUrl: './login.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginPage {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly modelo = signal<LoginModel>({ nombreUsuario: '', contrasena: '' });
  readonly formulario = form(this.modelo, (campo) => {
    required(campo.nombreUsuario, { message: 'El usuario es obligatorio.' });
    minLength(campo.nombreUsuario, 3, {
      message: 'El usuario debe tener al menos 3 caracteres.',
    });
    required(campo.contrasena, { message: 'La contraseña es obligatoria.' });
    minLength(campo.contrasena, 8, {
      message: 'La contraseña debe tener al menos 8 caracteres.',
    });
  });

  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);
  readonly mostrarContrasena = signal(false);
  readonly anio = new Date().getFullYear();

  errorDe = errorDe;

  async ingresar(event: Event): Promise<void> {
    event.preventDefault();
    this.error.set(null);
    this.cargando.set(true);

    try {
      await submit(this.formulario, {
        action: async () => {
          const { nombreUsuario, contrasena } = this.modelo();
          try {
            await firstValueFrom(this.auth.login(nombreUsuario.trim(), contrasena));
            const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') ?? '/dashboard';
            await this.router.navigateByUrl(returnUrl);
          } catch (error: unknown) {
            this.error.set(mensajeErrorLogin(error));
          }
        },
      });
    } finally {
      this.cargando.set(false);
    }
  }

  alternarContrasena(): void {
    this.mostrarContrasena.update((valor) => !valor);
  }
}
