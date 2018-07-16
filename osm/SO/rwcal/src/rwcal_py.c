
/*
 * 
 *   Copyright 2016 RIFT.IO Inc
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 *
 */

#include <libpeas/peas.h>

#include "rwcal-api.h"

rwcal_module_ptr_t rwcal_module_alloc()
{
  rwcal_module_ptr_t rwcal;

  rwcal = (rwcal_module_ptr_t)malloc(sizeof(struct rwcal_module_s));
  if (!rwcal)
    return NULL;

  bzero(rwcal, sizeof(struct rwcal_module_s));

  rwcal->framework = rw_vx_framework_alloc();
  if (!rwcal->framework)
    goto err;

  rw_vx_require_repository("RwCal", "1.0");

  goto done;

err:
  rwcal_module_free(&rwcal);

done:

  return rwcal;
}

void rwcal_module_free(rwcal_module_ptr_t * rwcal)
{
  if ((*rwcal)->cloud)
    g_object_unref((*rwcal)->cloud);

  free(*rwcal);
  *rwcal = NULL;

  return;
}
