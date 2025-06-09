# # Sales Access Control Module for Odoo 17

## 📋 Overview

This module extends Odoo's sales access control system to provide more flexible and hierarchical access management for sales orders. It addresses the limitation where only the primary salesperson can access their sales orders by implementing team-based and management-hierarchy access controls.

## 🎯 Business Problem Solved

**Current Limitation**: In standard Odoo, sales orders are only visible to the user listed as the "Salesperson" field, making collaboration and management oversight difficult.

**Solution**: This module implements a comprehensive access control system that allows:
- **Salespeople** to access orders where they are primary/secondary salesperson OR team members
- **Country Managers** to access all orders visible to salespeople they manage
- **Team-based access** where team members can see all team orders

## ✨ Key Features

### 1. **Secondary Salesperson**
- Add a "Secondary Salesperson" field to sales orders
- Both primary and secondary salespeople have full access to the order
- Track changes with built-in auditing

### 2. **Enhanced Team Management**
- Extend CRM Teams with "Team Members" functionality
- Team members automatically get access to all team orders
- Team leader is automatically added as a team member

### 3. **Country Manager Hierarchy**
- New "Sales Country Manager" model for hierarchical management
- Country Managers can oversee multiple salespeople across teams
- Managers inherit access to all orders visible to their managed salespeople

### 4. **Smart Access Control**
- Record rules ensure proper security at database level
- Performance-optimized with proper indexing
- Respects existing Odoo security groups and permissions

### 5. **Enhanced User Interface**
- New admin interfaces for managing team memberships
- Country Manager configuration screens
- Enhanced sales order views showing access information
- Statistics and reporting for access patterns

## 🏗️ Technical Architecture

### Data Model Relationships

```
┌─────────────┐    ┌─────────────────────┐    ┌─────────────┐
│ res.users   │    │ sales.country.      │    │ sale.order  │
│             │◄──►│ manager             │    │             │
│ (Salespeople│    │                     │    │ - user_id   │
│ & Managers) │    │ - manager_id        │    │ - secondary_│
└─────────────┘    │ - salespeople_ids   │    │   salesper  │
       ▲           └─────────────────────┘    │   son_id    │
       │                                      │ - team_id   │
       │           ┌─────────────────────┐    └─────────────┘
       └───────────│ crm.team            │            ▲
                   │                     │            │
                   │ - member_ids        │◄───────────┘
                   │ - user_id (leader)  │
                   └─────────────────────┘
```

### Key Models

#### 1. `sales.country.manager`
- **Purpose**: Define Country Manager to Salesperson relationships
- **Key Fields**:
  - `manager_id`: Many2one to res.users
  - `salespeople_ids`: Many2many to res.users
  - `active`: Boolean for archiving
  - `company_id`: Multi-company support

#### 2. `sale.order` (Extended)
- **New Fields**:
  - `secondary_salesperson_id`: Many2one to res.users
  - `accessible_user_ids`: Computed field showing all users with access

#### 3. `crm.team` (Extended)
- **New Fields**:
  - `member_ids`: Many2many to res.users
  - `member_count`: Computed field

### Security Implementation

#### Record Rules Strategy
1. **Admin Rule**: Full access for system administrators
2. **Sales Manager Rule**: Full access for sales managers
3. **Country Manager Rule**: Access to own orders + managed salespeople orders
4. **Salesperson Rule**: Access to own orders + team orders

#### Access Control Matrix
| User Role | Primary Orders | Secondary Orders | Team Orders | Managed Orders |
|-----------|----------------|------------------|-------------|----------------|
| Salesperson | ✅ | ✅ | ✅ | ❌ |
| Country Manager | ✅ | ✅ | ✅ | ✅ |
| Sales Manager | ✅ | ✅ | ✅ | ✅ |
| Admin | ✅ | ✅ | ✅ | ✅ |

## 🚀 Installation & Setup

### Prerequisites
- Odoo 17.0
- Standard `sale` and `sales_team` modules installed

### Installation Steps

1. **Download the module**:
   ```bash
   # Copy the sales_access_control folder to your addons directory
   cp -r sales_access_control /path/to/odoo/addons/
   ```

2. **Update apps list**:
   ```bash
   # In Odoo, go to Apps > Update Apps List
   ```

3. **Install the module**:
   ```bash
   # Search for "Sales Access Control" and click Install
   ```

4. **Configure security groups**:
   - Assign users to "Sales Country Manager" group as needed
   - Existing salespeople will automatically have the enhanced access

### Initial Configuration

#### 1. Set up Team Members
```
Sales > Sales Teams (Enhanced)
1. Open each sales team
2. Add team members in the "Team Members" field
3. Save - team leader is automatically added
```

#### 2. Configure Country Managers
```
Sales > Country Managers
1. Click "Create"
2. Select a Country Manager (user)
3. Add managed salespeople
4. Save
```

#### 3. Test Access (Recommended)
```
1. Create test sales orders with different salesperson combinations
2. Login as different users to verify access
3. Check the "Access Control" tab on sales orders
```

## 📊 Usage Examples

### Example 1: Team-based Access
```
Team: "Europe Sales"
Members: Alice, Bob, Charlie
Order: Customer X, Primary: Alice

Result: Alice, Bob, and Charlie can all access Customer X's order
```

### Example 2: Country Manager Access
```
Country Manager: John
Managed Salespeople: Alice, Bob
Orders: Alice has 5 orders, Bob has 3 orders

Result: John can access all 8 orders from Alice and Bob
```

### Example 3: Secondary Salesperson
```
Order: Customer Y
Primary Salesperson: Alice
Secondary Salesperson: Bob

Result: Both Alice and Bob have full access to Customer Y's order
```

## 🎛️ Admin Interface Guide

### Country Manager Management
- **Location**: Sales > Country Managers
- **Features**:
  - Create/edit country manager relationships
  - View statistics on managed salespeople
  - Access to all related sales orders
  - Archive inactive managers

### Enhanced Team Management
- **Location**: Sales > Sales Teams (Enhanced)
- **Features**:
  - Manage team memberships
  - View team statistics
  - Access team order overview
  - Automatic team leader inclusion

### Sales Order Views
- **Enhanced Features**:
  - "Access Control" tab showing all users with access
  - Secondary salesperson field
  - Access statistics and filters
  - Team-based filtering options

## ⚡ Performance Considerations

### Database Optimization
- **Indexing**: Added indexes on frequently queried fields
  - `sale_order.secondary_salesperson_id`
  - `crm_team.member_ids` relation table
- **Computed Fields**: Cached where appropriate to reduce calculation overhead

### Scalability Features
- **Efficient Queries**: Record rules use database-level filtering
- **Batch Processing**: Operations designed for handling large datasets
- **Memory Usage**: Computed fields stored when beneficial

### Performance Tips
```python
# Good: Use domain-based filters
orders = self.env['sale.order'].search([('team_id.member_ids', 'in', [user.id])])

# Avoid: Python-based filtering on large datasets
# This is automatically handled by the module's record rules
```

## 🚨 Security & Risk Management

### Security Features
- **Domain-based Security**: All access control at database level
- **Group-based Permissions**: Respects existing Odoo security groups
- **Audit Trail**: All changes tracked in standard Odoo chatter
- **Multi-company Support**: Proper company isolation

### Risk Mitigation

#### 1. **User Leaving Company**
**Risk**: Ex-employee retains access to orders
**Mitigation**: 
- Deactivate user account (standard Odoo)
- Update team memberships
- Archive country manager records

#### 2. **Over-permissive Access**
**Risk**: Users see orders they shouldn't
**Mitigation**:
- Regular access audits using built-in reports
- Principle of least privilege
- Clear team membership management

#### 3. **Performance Degradation**
**Risk**: Complex access rules slow down queries
**Mitigation**:
- Optimized record rules
- Database indexes on key fields
- Monitoring tools included

## 📈 Monitoring & Analytics

### Built-in Reports
- **User Access Summary**: Shows accessible orders per user
- **Team Performance**: Orders by team with access patterns
- **Manager Overview**: Country manager effectiveness metrics

### Key Metrics to Monitor
- **Orders per User**: Primary + Secondary + Team access
- **Access Patterns**: Most/least used access types
- **Team Effectiveness**: Orders closed by team vs individual effort

### Manual Testing Scenarios

#### Test 1: Basic Team Access
1. Create team with 2 members
2. Create order with primary salesperson = member 1
3. Login as member 2
4. Verify member 2 can access the order

#### Test 2: Country Manager Access
1. Create country manager with 2 salespeople
2. Create orders for both salespeople
3. Login as country manager
4. Verify manager can access both orders

#### Test 3: Secondary Salesperson
1. Create order with primary and secondary salesperson
2. Login as secondary salesperson
3. Verify full access to the order

## 🆘 Troubleshooting

### Common Issues

#### 1. **User Cannot See Expected Orders**
**Symptoms**: User should have access but orders don't appear
**Solutions**:
- Check user is in correct security group
- Verify team membership is saved
- Check country manager configuration
- Review record rule domain in debug mode

#### 2. **Performance Issues**
**Symptoms**: Slow order loading
**Solutions**:
- Check database indexes are created
- Review number of managed salespeople per manager
- Consider batch processing for large datasets

#### 3. **Access Too Restrictive**
**Symptoms**: Users can't access orders they need
**Solutions**:
- Add user to appropriate sales team
- Configure country manager relationship
- Check secondary salesperson field is set

### Debug Tools
```python
# Check user access in Python console
user = env['res.users'].browse(USER_ID)
domain = env['sale.order']._get_user_access_domain(USER_ID)
accessible_orders = env['sale.order'].search(domain)
print(f"User {user.name} can access {len(accessible_orders)} orders")
```

### Support & Community
- **Issues**: Report bugs via GitHub issues
## 📋 Changelog

### Version 17.0.1.0.0
- Initial release
- Basic team member access control
- Country manager hierarchy
- Secondary salesperson functionality
- Enhanced UI and reporting
- Demo data and documentation