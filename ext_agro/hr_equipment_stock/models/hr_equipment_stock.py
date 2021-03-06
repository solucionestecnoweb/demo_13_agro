# -*- coding: utf-8 -*-
# from openerp import models, fields, api, _
# from openerp.exceptions import UserError, AccessError
# from openerp.exceptions import Warning

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from odoo.exceptions import Warning

"""class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    prestamo_id=fields.Many2one('hr.prestamo', string='Lineas de Prestamos')
    status_prestamo=fields.Selection(selection=[('hold','En Espera'),('granted','Otorgado'),('solvent','Solvente')],default='hold')
    prestamo_activo = fields.Boolean(default=False)
    descuento_prestamo_activo = fields.Boolean(default=False)
    acumulado = fields.Float(compute='_compute_acumulado')
    acumulado_gps = fields.Float(compute='_compute_acumulado_gps')
    disponible = fields.Float(compute='_compute_disponible')
    tasa_int = fields.Float(compute='_compute_tasa_bcv')
    acumulado_int = fields.Float(compute='_compute_acumulado_int')
    custom_currency_id = fields.Many2one(
        'res.currency', 
        default=lambda self: self.env.user.company_id.currency_id, 
        string='Currency', 
        readonly=True
    )
    dias_vacaciones = fields.Integer(string="Dias de disfrutes por tiempo de servicios", compute='_compute_dias_vacaciones')
    tiempo_antiguedad = fields.Integer(string="Tiempo de Antiguedad (años)", compute='_compute_tiempo_antiguedad')
    tiempo_antiguedad_dias = fields.Integer()
    tiempo_fraccion_dias = fields.Integer()
    tiempo_fraccion_meses =fields.Integer()
    dias_totales_disfrutados = fields.Integer(compute='_compute_dias_disfrutar')
    dias_restantes_disfrutar = fields.Integer(compute='_compute_dias_restantes')
    date_actual = fields.Date(string='Date From', compute='_compute_fecha_hoy')
    salario_integral_diario = fields.Float(compute='_compute_salario_integral_diario')
    zapatos = fields.Selection([('32','32'),('33','33'),('34','34'),('35','35'),('36','36'),('37','37'),('38','38'),('39','39'),('40','40'),('41','41'),('42','42'),('43','43'),('44','44'),('45','45'),('46','46')])
    camisas = fields.Selection([('XS', 'XS'),('S', 'S'),('M', 'M'),('M-L', 'M-L'),('L', 'L'),('L-XL', 'L-XL'),('XL', 'XL'),('XL-XXL', 'XL-XXL'),('XXL', 'XXL')])
    pantalon = fields.Selection([('24','24'),('25','25'),('26','26'),('27','27'),('28','28'),('29','29'),('30','30'),('31','31'),('32','32'),('33','33'),('34','34'),('35','35'),('36','36'),('37','37'),('38','38'),('39','39'),('40','40'),('41','41'),('42','42'),('43','43'),('44','44'),('45','45'),('46','46')])
    chemise = fields.Selection([('XS', 'XS'),('S', 'S'),('M', 'M'),('M-L', 'M-L'),('L', 'L'),('L-XL', 'L-XL'),('XL', 'XL'),('XL-XXL', 'XL-XXL'),('XXL', 'XXL')])
    """
class HrEquipmentRequest(models.Model):
    _inherit = 'maintenance.request'

    #@api.depends('employee_id')
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for selff in self:
            selff.custom_location_id = selff.employee_id.department_id.custom_location_id.id

    custom_need_po = fields.Boolean(string="Need PO",help="Tick this box if you want to create Purchase Request", defaults=False)
    custom_need_move = fields.Boolean(string="Need Move",help="Tick this box if you want to create Move", defaults=False)
    custom_equipment_line1 = fields.One2many('equipment.parts.line','request_id1', 'Equipment Parts line')
    custom_equipment_line2 = fields.One2many('equipment.parts.line','request_id2', 'Equipment Parts line')
    custom_needed_parts = fields.One2many('equipment.parts.line','request_id3', 'Needed Parts')
    custom_location_id = fields.Many2one('stock.location','Department Location')
    custom_maintainer_location_id = fields.Many2one('stock.location','Maintainer Location')
    custom_move_done = fields.Boolean()
    custom_po_done = fields.Boolean()


    # @api.multi #odoo13
    def parts_operation(self):
        po = []
        transfer = []
        for need_parts in self.custom_needed_parts:
            if need_parts.product_stock > 0:
                if need_parts.qty > need_parts.product_stock:
                    if need_parts.compute_done == False:
                        po.append((0,False,{'product_id':need_parts.product_id.id,
                                        'qty':need_parts.qty - need_parts.product_stock}))
                        transfer.append((0,False,{'product_id':need_parts.product_id.id,
                                        'qty':need_parts.product_stock}))
                        need_parts.compute_done = True
                        
                if need_parts.qty < need_parts.product_stock:
                    if need_parts.compute_done == False:
                        transfer.append((0,False,{'product_id':need_parts.product_id.id,
                                        'qty':need_parts.qty}))
                        need_parts.compute_done = True
                    
            if need_parts.product_stock <= 0:
                if need_parts.compute_done == False:
                    po.append((0,False,{'product_id':need_parts.product_id.id, 'qty':need_parts.qty}))
                    need_parts.compute_done = True
        self.custom_equipment_line1 = po
        self.custom_equipment_line2 = transfer
        return True

    # @api.multi #odoo13
    def create_purchase_requisition(self):
        partlist = []
        for line in self.custom_equipment_line1:
            if not line.compute_done:
                partlist.append((0,False,{
                    'product_id':line.product_id.id,
                    'product_qty':line.qty,
                    'product_uom_id':line.product_id.uom_id.id,
                    'schedule_date':fields.Date.context_today(self),
                }))
                line.compute_done = True 
        if not partlist:
            raise Warning(_('Purchase requisition is already created!'))
        if partlist:
            create_id = self.env['purchase.requisition'].create(
                {
                    'line_ids':partlist,
                    # 'exclusive':'multiple', 
                    'origin':self.name,
                    'custom_equipment_request_id':self.id, 
                    'description':self.name
                })


    @api.model
    def _get_warehouse(self):
        warehouse = self.env['stock.warehouse'].search([('partner_id','=',self.env.user.company_id.partner_id.id)])
        return warehouse[0].id if warehouse else False

    @api.model
    def _get_company_location(self):
        try:
            location_id = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_stock')[1]
            self.env['stock.location'].check_access_rule('read')
        except (AccessError, ValueError):
            location_id = False
        return location_id

    @api.model
    def _get_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        #types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id),])
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)])
        return types[0].id if types else False

    @api.model
    def _prepare_picking(self):
        if self._get_picking_type() == False:
            raise Warning(_('Please setup Picking Type.'))
        if not self.custom_maintainer_location_id:
            raise Warning(_("Please choose Maintainer Location"))
        return {
            'picking_type_id': self._get_picking_type(),
            'partner_id': self.user_id.id,
            'date': self.request_date,
            'origin': self.name,
            'location_id': self._get_company_location(),
            'location_dest_id': self.custom_maintainer_location_id.id,
            'custom_equipment_request_id':self.id,
        }

    # @api.multi #odoo13
    def _crete_move_line(self):
        lines = []
        for line in self.custom_equipment_line2:
            if not line.compute_done:
                template = {
                    'name': self.name or '',
                    'product_id': line.product_id.id,
                    'product_uom_qty':line.qty,
                    'product_uom': line.product_id.uom_id.id,
                    'date': self.request_date,
                    'date_expected': self.request_date,
                    'location_id': self._get_company_location(),
                    'location_dest_id': self.custom_maintainer_location_id.id,
                    #'picking_id': picking.id,
                    'partner_id': self.user_id.id,
                    # 'move_dest_id': False,
                    'state': 'draft',
                    'purchase_line_id': False,
                    'company_id': self.env.user.company_id.id,#line.order_id.company_id.id,
                    'price_unit': line.product_id.standard_price,
                    'picking_type_id': self._get_picking_type(),
                    'group_id': False,
                    # 'procurement_id': False,
                    'origin': self.name,
                    'route_ids': False,#line.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                    'warehouse_id':self._get_warehouse(),#line.order_id.picking_type_id.warehouse_id.id,
                }   
                line.compute_done = True 
                lines.append(template)
        return lines

    # @api.multi #odoo13
    def create_picking(self):
        for order in self:
            moves = self._crete_move_line()
            res = order._prepare_picking()
            if not moves:
                raise Warning(_('Moves are already created.'))
            if moves:
                picking = self.env['stock.picking'].create(res)
                for val in moves:
                    val.update({'picking_id': picking.id})
                    self.env['stock.move'].create(val)
        return True 
        
    def action_view_internal_transfer(self, cr, uid, ids, context=None):
        template_obj = self.pool.get("product.template")
        templ_ids = list(set([x.product_tmpl_id.id for x in self.browse(cr, uid, ids, context=context)]))
        return template_obj.action_view_routes(cr, uid, templ_ids, context=context)

class hr_department(models.Model):
    _inherit = 'hr.department'
    custom_location_id = fields.Many2one('stock.location','Department Location')

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    custom_equipment_request_id = fields.Many2one('maintenance.request','Equipment request id')
    
class purchase_requisition(models.Model):
    _inherit = 'purchase.requisition'
    custom_equipment_request_id = fields.Many2one('maintenance.request','Equipment request id')

class equipment_parts_line(models.Model):
    _name = 'equipment.parts.line'

    @api.onchange('product_id')
    def _product_qty(self):
        self.product_stock = self.product_id.qty_available

    product_id = fields.Many2one('product.product','Product')
    qty = fields.Float(string="Quantity")
    compute_done = fields.Boolean(string="Compute Done")
    product_stock = fields.Float(string="Product Stock")
    request_id1 = fields.Many2one('maintenance.request','PO line id')
    request_id2 = fields.Many2one('maintenance.request','Transfer id')
    request_id3 = fields.Many2one('maintenance.request','Needed Parts Id')

