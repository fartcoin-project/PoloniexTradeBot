# shared-prefs-plugin

Getter and setter of preferences

## Install

```bash
npm install shared-prefs-plugin
npx cap sync
```

## API

<docgen-index>

* [`getPreference(...)`](#getpreference)
* [`setPreference(...)`](#setpreference)

</docgen-index>

<docgen-api>
<!--Update the source file JSDoc comments and rerun docgen to update the docs below-->

### getPreference(...)

```typescript
getPreference(options: { key: string; }) => Promise<{ value: string; }>
```

| Param         | Type                          |
| ------------- | ----------------------------- |
| **`options`** | <code>{ key: string; }</code> |

**Returns:** <code>Promise&lt;{ value: string; }&gt;</code>

--------------------


### setPreference(...)

```typescript
setPreference(options: { key: string; value: string; }) => Promise<void>
```

| Param         | Type                                         |
| ------------- | -------------------------------------------- |
| **`options`** | <code>{ key: string; value: string; }</code> |

--------------------

</docgen-api>
