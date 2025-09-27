// DataTables initialization module
import 'datatables.net-bs5';

export function initializeDataTables() {
  // Default DataTables configuration
  const defaultConfig = {
    language: {
      url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/es-ES.json'
    },
    responsive: true,
    pageLength: 25,
    lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, 'Todos']],
    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
         '<"row"<"col-sm-12"tr>>' +
         '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
    order: [[0, 'desc']],
    columnDefs: [
      {
        targets: 'no-sort',
        orderable: false
      },
      {
        targets: 'text-center',
        className: 'text-center'
      },
      {
        targets: 'text-right',
        className: 'text-end'
      }
    ],
    drawCallback: function() {
      // Reinitialize tooltips after table redraw
      const tooltipTriggerList = [].slice.call(this.api().table().container().querySelectorAll('[data-bs-toggle="tooltip"]'));
      tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
      });
    }
  };

  // Initialize basic DataTables
  $('.datatable').each(function() {
    const $table = $(this);
    const config = { ...defaultConfig };
    
    // Check for custom configuration
    if ($table.data('config')) {
      Object.assign(config, $table.data('config'));
    }
    
    $table.DataTable(config);
  });

  // Initialize students table with custom configuration
  if ($('#estudiantes-table').length) {
    $('#estudiantes-table').DataTable({
      ...defaultConfig,
      ajax: {
        url: '/api/estudiantes',
        type: 'GET',
        dataSrc: 'data'
      },
      columns: [
        { data: 'rut', title: 'RUT' },
        { data: 'nombre_completo', title: 'Nombre Completo' },
        { data: 'carrera', title: 'Carrera' },
        { data: 'nivel', title: 'Nivel' },
        { data: 'estado', title: 'Estado' },
        {
          data: null,
          title: 'Acciones',
          orderable: false,
          render: function(data, type, row) {
            return `
              <div class="btn-group" role="group">
                <a href="/estudiantes/${row.id}" class="btn btn-sm btn-outline-primary" title="Ver">
                  <i class="fas fa-eye"></i>
                </a>
                <a href="/estudiantes/${row.id}/edit" class="btn btn-sm btn-outline-secondary" title="Editar">
                  <i class="fas fa-edit"></i>
                </a>
                <button type="button" class="btn btn-sm btn-outline-danger delete-btn" data-id="${row.id}" title="Eliminar">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            `;
          }
        }
      ],
      columnDefs: [
        {
          targets: [4],
          render: function(data, type, row) {
            const statusClass = data === 'Activo' ? 'success' : 'secondary';
            return `<span class="badge bg-${statusClass}">${data}</span>`;
          }
        }
      ]
    });
  }

  // Initialize apoyos table with custom configuration
  if ($('#apoyos-table').length) {
    $('#apoyos-table').DataTable({
      ...defaultConfig,
      ajax: {
        url: '/api/apoyos',
        type: 'GET',
        dataSrc: 'data'
      },
      columns: [
        { data: 'codigo', title: 'Código' },
        { data: 'estudiante_nombre', title: 'Estudiante' },
        { data: 'tipo_apoyo', title: 'Tipo de Apoyo' },
        { data: 'monto', title: 'Monto' },
        { data: 'fecha_inicio', title: 'Fecha Inicio' },
        { data: 'estado', title: 'Estado' },
        {
          data: null,
          title: 'Acciones',
          orderable: false,
          render: function(data, type, row) {
            return `
              <div class="btn-group" role="group">
                <a href="/apoyos/${row.id}" class="btn btn-sm btn-outline-primary" title="Ver">
                  <i class="fas fa-eye"></i>
                </a>
                <a href="/apoyos/${row.id}/edit" class="btn btn-sm btn-outline-secondary" title="Editar">
                  <i class="fas fa-edit"></i>
                </a>
                <button type="button" class="btn btn-sm btn-outline-danger delete-btn" data-id="${row.id}" title="Eliminar">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            `;
          }
        }
      ],
      columnDefs: [
        {
          targets: [3],
          render: function(data, type, row) {
            return window.SynapsisApp.utils.formatCurrency(data);
          }
        },
        {
          targets: [4],
          render: function(data, type, row) {
            return window.SynapsisApp.utils.formatDate(data);
          }
        },
        {
          targets: [5],
          render: function(data, type, row) {
            let statusClass = 'secondary';
            switch (data) {
              case 'Activo':
                statusClass = 'success';
                break;
              case 'Pendiente':
                statusClass = 'warning';
                break;
              case 'Finalizado':
                statusClass = 'info';
                break;
              case 'Cancelado':
                statusClass = 'danger';
                break;
            }
            return `<span class="badge bg-${statusClass}">${data}</span>`;
          }
        }
      ]
    });
  }

  // Initialize tecnicos table with custom configuration
  if ($('#tecnicos-table').length) {
    $('#tecnicos-table').DataTable({
      ...defaultConfig,
      ajax: {
        url: '/api/tecnicos',
        type: 'GET',
        dataSrc: 'data'
      },
      columns: [
        { data: 'rut', title: 'RUT' },
        { data: 'nombre_completo', title: 'Nombre Completo' },
        { data: 'email', title: 'Email' },
        { data: 'especialidad', title: 'Especialidad' },
        { data: 'estado', title: 'Estado' },
        {
          data: null,
          title: 'Acciones',
          orderable: false,
          render: function(data, type, row) {
            return `
              <div class="btn-group" role="group">
                <a href="/tecnicos/${row.id}" class="btn btn-sm btn-outline-primary" title="Ver">
                  <i class="fas fa-eye"></i>
                </a>
                <a href="/tecnicos/${row.id}/edit" class="btn btn-sm btn-outline-secondary" title="Editar">
                  <i class="fas fa-edit"></i>
                </a>
                <button type="button" class="btn btn-sm btn-outline-danger delete-btn" data-id="${row.id}" title="Eliminar">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            `;
          }
        }
      ],
      columnDefs: [
        {
          targets: [4],
          render: function(data, type, row) {
            const statusClass = data === 'Activo' ? 'success' : 'secondary';
            return `<span class="badge bg-${statusClass}">${data}</span>`;
          }
        }
      ]
    });
  }

  // Handle delete buttons
  $(document).on('click', '.delete-btn', function() {
    const id = $(this).data('id');
    const table = $(this).closest('table').DataTable();
    
    Swal.fire({
      title: '¿Estás seguro?',
      text: 'Esta acción no se puede deshacer',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar'
    }).then((result) => {
      if (result.isConfirmed) {
        // Perform delete action
        const url = window.location.pathname.includes('estudiantes') ? `/api/estudiantes/${id}` :
                   window.location.pathname.includes('apoyos') ? `/api/apoyos/${id}` :
                   `/api/tecnicos/${id}`;
        
        fetch(url, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            table.ajax.reload();
            Swal.fire('Eliminado', 'El registro ha sido eliminado', 'success');
          } else {
            Swal.fire('Error', data.message || 'Error al eliminar el registro', 'error');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          Swal.fire('Error', 'Error al eliminar el registro', 'error');
        });
      }
    });
  });

  // Export functionality
  window.exportTable = function(format, tableId = null) {
    const table = tableId ? $(`#${tableId}`).DataTable() : $('.datatable').DataTable();
    
    switch (format) {
      case 'excel':
        table.button('.buttons-excel').trigger();
        break;
      case 'pdf':
        table.button('.buttons-pdf').trigger();
        break;
      case 'csv':
        table.button('.buttons-csv').trigger();
        break;
      case 'print':
        table.button('.buttons-print').trigger();
        break;
    }
  };

  console.log('DataTables initialized');
}